import re
from calibre import strftime
from calibre.web.feeds.recipes import BasicNewsRecipe


class Poche(BasicNewsRecipe):

    app_url = 'http://app.inthepoche.com'  # self-hosted or managed poche
    contents_key = 'domain'  # [domain|read-time]

    title = 'Poche'
    __author__ = 'Xavier Detant, Dmitry Sandalov'
    description = 'Gets articles from your poche server'
    needs_subscription = True
    remove_tags_before = dict(id='article')
    remove_tags_after = dict(id='article')

    def get_browser(self):
        br = BasicNewsRecipe.get_browser(self)
        self.authentify_to_poche(br)
        return br

    def parse_index(self):

        articles = {}
        key = None
        ans = []

        base_url = self.get_base_url()
        soup = self.index_to_soup(base_url)
        pageCounter = PageCounter(soup)
        # stop if no more articles or reached max articles limit
        while not pageCounter.is_max_reached():

            # open poche on desired page
            soup = self.index_to_soup(
                base_url + "?view=home&sort=id&p=" + str(pageCounter.current_page_number()))

            # extract articles from entrie divs, articles num from nb-results
            for div in soup.findAll(True, attrs={
                    'class': ['entrie']}):

                # continue if no article link
                a = div.find('a', href=True)
                if not a:
                    continue

                # extract article info
                key = self.get_contents_key(div)
                url = base_url + a['href']
                title = self.tag_to_string(a, use_alt=False)
                description = url
                pubdate = strftime('%a, %d %b')
                summary = div.find('p')
                if summary:
                    description = self.tag_to_string(summary, use_alt=False)
                feed = key if key else 'Uncategorized'
                if not feed in articles.keys():
                    articles[feed] = []

                # finally put articles to list
                articles[feed].append(dict(
                    title=title, url=url, date=pubdate,
                    description=description, content=''))
                pageCounter.article_added()

                if pageCounter.is_max_reached():
                    print "Max reached"
                    break

            pageCounter.page_treated()

        ans = [(key, articles[key]) for key in articles.keys()]
        return ans

    def authentify_to_poche(self,browser):
        """Login into poche application submitting the login form using the given username and password"""
        if self.username and self.password:
            base_url = self.get_base_url()
            browser.open(base_url)
            browser.select_form(name='loginform')
            browser['login'] = self.username
            browser['password'] = self.password
            browser.submit()

    def get_base_url(self):
        """Gets poche base url. """
        url = self.app_url + '/u/' + self.username + '/' \
            if self.app_url == 'http://app.inthepoche.com' \
            else self.app_url + '/'  # self-hosted poche
        return url


    def get_contents_key(self, div):
        """Gets key tag from article. """
    
        if self.contents_key == 'read-time':
            a_class = 'reading-time'
        else:
            a_class = 'tool link'
    
        key = self.tag_to_string(div.find(
            'a', attrs={'class': [a_class]}))
        return key

class PageCounter():
    page_count = 1
    articles_count = 0
    articles_number = 1
    max_articles = 15
    
    def __init__(self,indexPage):
        nb_results = indexPage.find(True, attrs={'class': 'nb-results'})
        if nb_results != None:
            self.articles_number = int(re.findall(r'\d+', nb_results.string)[0])

    def is_max_reached(self):
        "True if the max number of article has been reached"
        return ((self.articles_count >= self.max_articles) or (self.articles_count >= self.articles_number))

    def article_added(self):
        self.articles_count += 1

    def page_treated(self):
        self.page_count += 1

    def current_page_number(self):
        return self.page_count
