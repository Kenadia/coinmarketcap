import logging
import time

import bs4
import requests

import sms

URL = 'https://coinmarketcap.com/currencies/ethereum/#markets'
PRICE_COUMN = 'Price'
SOURCE_COLUMN = 'Source'
VOLUME_COLUMN = 'Volume (24h)'

_LOG = logging.getLogger(__name__)

RECIPIENTS = {
}


def parse(value, heading):
  if heading in (VOLUME_COLUMN, PRICE_COUMN):
    return money_to_float(value)
  return value


def money_to_float(money):
  stripped = money.strip().lstrip('$').replace(',', '')
  try:
    return float(stripped)
  except ValueError:
    raise ValueError('Could not parse money value `%s`' % money)


def extract_table(url, table_index, parse_fn=None):
  if parse_fn is None:
    parse_fn = lambda value, heading: value

  html = requests.get(url)

  if not html.ok:
    raise RuntimeError('Got error in request')

  soup = bs4.BeautifulSoup(html.text, 'html.parser')
  tables = soup.find_all('table')

  if table_index < 0 or table_index >= len(tables):
    raise ValueError('Invalid table index, found %d tables' % len(tables))

  table = tables[table_index]
  headings = [th.get_text() for th in table.find('tr').find_all('th')]
  rows = []
  skipped_rows = 0

  for raw_row in table.find_all('tr')[1:]:
    values = (td.get_text() for td in raw_row.find_all('td'))
    row = {}

    try:
      for heading, value in zip(headings, values):
        row[heading] = parse(value, heading)
    except ValueError:
      skipped_rows += 1
      continue

    rows.append(row)

  if skipped_rows:
    _LOG.warn('Skipped %d of %d rows', skipped_rows, skipped_rows + len(rows))

  return rows


def get_price_info():
  rows = extract_table(URL, 0, parse)

  gdax_row = [row for row in rows if row[SOURCE_COLUMN] == 'GDAX'][0]
  gdax_price = gdax_row[PRICE_COUMN]

  total_volume = sum(row[VOLUME_COLUMN] for row in rows)
  numerator = sum(row[VOLUME_COLUMN] * row[PRICE_COUMN] for row in rows)
  weighted_avg_price = numerator / total_volume

  premium = (gdax_price  - weighted_avg_price) / weighted_avg_price * 100

  return gdax_price, weighted_avg_price, premium


if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)

  client = sms.Client()

  start = time.time()
  while True:
    elapsed = int(time.time() - start)

    recipients = [number for number, interval in RECIPIENTS.iteritems()
                  if elapsed % interval == 0]

    if recipients:
      message = 'GDAX: %.2f avg: %.2f -- %+.1f%%' % get_price_info()
      _LOG.info('Sending to %d recipients: %s', len(recipients), message)

      for recipient in recipients:
        client.send(recipient, message)

    time.sleep(1)
