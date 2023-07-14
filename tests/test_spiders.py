from disboard.spiders.servers import ServersSpider


def test_parse(settings, sample_response, blocked_response):
    # Create an instance of the spider
    spider = ServersSpider()
    spider.settings = settings

    # Call the parse method of the spider with the sample response
    results = list(spider.parse(sample_response))

    assert len(results) > 0
