import re
from calibre import strftime
from calibre.web.feeds.recipes import BasicNewsRecipe


class Poche(BasicNewsRecipe):

    app_url = 'http://app.inthepoche.com'
    max_articles_per_feed = 15

    title = 'Poche'
    __author__ = 'Xavier Detant'
    description = 'Ma poche'
    needs_subscription = True
    remove_tags_before = dict(id='article')
    remove_tags_after = dict(id='article')

    def get_browser(self):
        br = BasicNewsRecipe.get_browser(self)

        # poche login
        if self.username and self.password:
            br.open(self.app_url + '/u/' + self.username) \
                if self.app_url == 'http://app.inthepoche.com' \
                else br.open(self.app_url)  # self-hosted poche

            # submit the login form using credentials
            br.select_form(name='loginform')
            br['login'] = self.username
            br['password'] = self.password
            br.submit()

        return br

    def parse_index(self):

        base_url = self.app_url + '/u/' + self.username + '/' \
            if self.app_url == 'http://app.inthepoche.com' \
            else self.app_url  # self-hosted poche

        # init values before loop
        page_count = 1  # poche page iterator
        articles_count = 0  # extracted articles counter
        articles_number = 1  # total articles in poche library

        articles = {}
        key = None
        ans = []

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

                # use reading time as a key
                key = self.tag_to_string(div.find(
                    'a', attrs={'class': ['reading-time']}))

                # extract article info
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
