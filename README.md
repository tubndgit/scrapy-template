# Scrapy Template

Required:
- Python version >=2.7
- Scrapy installed
- Selenium installed

# Install required libs

`pip install -r requirements.txt`

# Install luminati (Optional)

View at https://github.com/luminati-io/luminati-proxy

`wget -qO- https://luminati.io/static/lpm/luminati-proxy-latest-setup.sh | bash`

Run as daemon:

`luminati --daemon`

Point your browser to the app admin UI http://your_host:22999 to set up credentials and configure your proxies.

Luminati config file: `luminati_proxy_manager/.luminati.json`

Sample luminati config in file `.luminati_sample.json`

# Configure Script

- Rename folder `config.sample` to `config`

- Open `config/common.json` and change the settings

# Run scraper:

- Active your virtual environment:

`source /root/henry/env/bin/activate`

`scrapy crawl domain_name`
