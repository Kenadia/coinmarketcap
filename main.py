import logging

import bs4
import requests


_LOG = logging.getLogger(__name__)


def money_to_float(money):
  stripped = money.strip().lstrip('$').replace(',', '')
  try:
    return float(stripped)
  except ValueError:
    raise ValueError('Could not parse money value `%s`' % money)


def main():
  url = 'https://coinmarketcap.com/currencies/ethereum/#markets'
  html = requests.get(url)

  if not html.ok:
    raise ValueError('Got error in request')

  soup = bs4.BeautifulSoup(html.text)
  tables = soup.find_all('table')

  if len(tables) > 1:
    _LOG.warn('HTML contained more than one table element')

  table_index = 0
  table = tables[table_index]

  def parse(value, heading):
    if heading in ('Volume (24h)', 'Price'):
      return money_to_float(value)
    return value

  headings = [th.get_text() for th in table.find('tr').find_all('th')]
  rows = []

  for raw_row in table.find_all('tr')[1:]:
    values = (td.get_text() for td in raw_row.find_all('td'))
    row = {}

    try:
      for heading, value in zip(headings, values):
        row[heading] = parse(value, heading)
    except ValueError:
      continue

    rows.append(row)

  return rows

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  rows = main()
