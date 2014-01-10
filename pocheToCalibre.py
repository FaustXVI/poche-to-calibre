import re
from calibre import strftime
from calibre.web.feeds.recipes import BasicNewsRecipe


class Poche(BasicNewsRecipe):

    app_url = 'http://app.inthepoche.com'  # self-hosted or managed poche
    max_articles_per_feed = 15  # articles in output file
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

        # init values before loop
        page_count = 1  # poche page iterator
        articles_count = 0  # extracted articles counter
        articles_number = 1  # total articles in poche library

        articles = {}
        key = None
        ans = []

        base_url = self.get_base_url()

        # stop if no more articles or reached max articles limit
        while ((articles_count < self.max_articles_per_feed) and
               (articles_count < articles_number)):

            # open poche on desired page
            soup = self.index_to_soup(
                base_url + "?view=home&sort=id&p=" + str(page_count))

            # extract articles from entrie divs, articles num from nb-results
            for div in soup.findAll(True, attrs={
                    'class': ['entrie', 'nb-results']}):

                # get total articles in poche lib
                if div['class'] == 'nb-results':
                    articles_number = int(re.findall(r'\d+', div.string)[0])

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
                articles_count += 1

                # exit loop if max_articles_per_feed exceeded
                if not ((articles_count < self.max_articles_per_feed) and
                        (articles_count < articles_number)):
                    break
            page_count += 1

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
