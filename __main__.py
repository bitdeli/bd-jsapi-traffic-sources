from bitdeli.widgets import set_theme, Description, Title
from bitdeli.chain import Profiles
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from urlparse import urlsplit, urlunsplit

set_theme('bank')

TIMELINE_DAYS = 30
TFORMAT = '%Y-%m-%d'

text = {'window': TIMELINE_DAYS}
limit = datetime.now() - timedelta(days=TIMELINE_DAYS)
limit_str = limit.strftime(TFORMAT)


def recent_views(pageviews):
    for pageview in pageviews:
        day = pageview[0].split('T')[0]
        if day >= limit_str:
            yield pageview


def referrers(profiles):
    def domains(pageviews):
        referrers = defaultdict(Counter)
        for pageview in pageviews:
            page_info = pageview[3].get("$page_info")
            if not page_info or "referrer" not in page_info:
                continue
            url = urlsplit(page_info["referrer"])
            clean = urlunsplit(("", url.netloc, url.path,
                                url.query, "")).strip("/")
            referrers[url.netloc][clean] += 1
        return referrers

    def top_urls(referrers):
        for domain, urls in referrers.iteritems():
            top_page = urls.most_common(1)[0]
            yield {'Domain': domain,
                   'Domain Visits': len(list(urls.elements())),
                   'Top Page': top_page[0],
                   'Visits': top_page[1]}

    referrers = defaultdict(Counter)
    for profile in profiles:
        if '$pageview' not in profile:
            continue
        pageviews = recent_views(profile['$pageview'])
        for domain, urls in domains(pageviews).iteritems():
            referrers[domain].update(urls)

    yield {'type': 'table',
           'label': 'Top Referrers',
           'data': sorted(list(top_urls(referrers)),
                          key=lambda r: -r['Domain Visits'])[:20],
           'size': (12, 4),
           'csv_export': True}


def activity(profiles):
    def recent_days(pageviews):
        return [pv[0].split('T')[0] for pv in recent_views(pageviews)]

    def timeline(stats):
        for i in range(TIMELINE_DAYS + 1):
            day = (limit + timedelta(days=i)).strftime(TFORMAT)
            yield day, stats[day]

    def top_day(uniques):
        top_day = uniques.most_common(1)[0]
        return (datetime.strptime(top_day[0], TFORMAT).strftime('%B %d'),
                top_day[1])

    pageviews = Counter()
    uniques = Counter()
    for profile in profiles:
        if '$pageview' not in profile:
            continue
        pageviews.update(recent_days(profile['$pageview']))
        uniques.update(frozenset(recent_days(profile['$pageview'])))

    if uniques:
        text['top_day'] = top_day(uniques)
    text['total'] = len(list(uniques.elements()))

    Title("{total} daily unique visitors in total "
          "over the last {window} days",
          text)
    if 'top_day' in text:
        Description("{top_day[0]} was the most active day with "
                    "{top_day[1]} unique visitors.",
                    text)

    yield {'type': 'line',
           'label': 'Daily Visitors',
           'data': [{'label': 'Pageviews',
                     'data': list(timeline(pageviews))},
                    {'label': 'Unique Visitors',
                     'data': list(timeline(uniques))}],
           'size': (12, 4)}


Profiles().map(referrers).show()

Profiles().map(activity).show()
