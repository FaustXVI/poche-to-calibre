import re
from calibre import strftime
from calibre.web.feeds.recipes import BasicNewsRecipe


class Poche(BasicNewsRecipe):

    app_url = 'http://app.inthepoche.com'  # self-hosted or managed poche

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

    def authentify_to_poche(self,browser):
        """Login into poche application submitting the login form using the given username and password"""
        if self.username and self.password:
            base_url = self.get_base_url()
            browser.open(base_url)
            browser.select_form(name='loginform')
            browser['login'] = self.username
            browser['password'] = self.password
            browser.submit()

    def parse_index(self):
        base_url = self.get_base_url()
        soup = self.index_to_soup(base_url)
        pageCounter = PageCounter(soup)
        pageParser = PageParser(pageCounter,base_url,self)

        while not pageCounter.is_max_reached():
            page_url = base_url + "?view=home&sort=id&p=" + str(pageCounter.current_page_number())
            soup = self.index_to_soup(page_url)
            pageParser.parse(soup)
            pageCounter.page_treated()

        return pageParser.get_articles()

    def get_base_url(self):
        """Gets poche base url. """
        url = self.app_url + '/u/' + self.username + '/' \
            if self.app_url == 'http://app.inthepoche.com' \
            else self.app_url + '/'  # self-hosted poche
        return url

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

class PageParser():

    contents_key = 'domain'  # [domain|read-time]
    articles = {}
    ans = []
    pageCounter = None
    base_url = None
    browser = None

    def __init__(self,pageCounter,base_url,browser):
        self.pageCounter = pageCounter
        self.base_url = base_url
        self.browser = browser
    
    def parse(self,page):
        for div in page.findAll(True, attrs={'class': ['entrie']}):
            key = self.get_contents_key(div)
            article = self.extract_info(div)
            if article:
                self.add_article(key,article)
            if self.pageCounter.is_max_reached():
                print "Max reached"
                break

    def extract_info(self,div):
        a = div.find('a', href=True)
        if a:
            url = self.base_url + a['href']
            title = BasicNewsRecipe.tag_to_string(a, use_alt=False)
            description = url
            pubdate = strftime('%a, %d %b')
            summary = div.find('p')
            if summary:
                description = BasicNewsRecipe.tag_to_string(summary, use_alt=False)
            return dict(title=title, url=url, date=pubdate,description=description, content='') 

    def add_article(self,key,article):
        feed = self.get_category(key)
        if not feed in self.articles.keys():
            self.articles[feed] = []
        self.articles[feed].append(article)
        self.pageCounter.article_added()
        

    def get_category(self,key):
        return key if key else 'Uncategorized'

    def get_contents_key(self, div):
        """Gets key tag from article. """
    
        if self.contents_key == 'read-time':
            key_tag = div.find('a', attrs={'class': ['reading-time']})
        else:
            url = 'http://' + BasicNewsRecipe.tag_to_string(div.find('a', attrs={'class': ['tool link']}))
            soup = self.browser.index_to_soup(url)
            key_tag = soup.find('title')

        return BasicNewsRecipe.tag_to_string(key_tag)

    def get_articles(self):
        return [(key, self.articles[key]) for key in self.articles.keys()]
