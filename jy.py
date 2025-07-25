import scrapy
from shanghai.items import ShanghaiItem

class JySpider(scrapy.Spider):
    name = "jy"
    allowed_domains = ["shggzy.com"]
    start_urls = ["https://www.shggzy.com/jyxxgc"]

    custom_settings = {
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15'
        }
    }

    max_page = 1000

    def parse(self, response):
        # 1. 模拟点击第二个选项卡（li[2]）
        # 假设点击 li[2] 会跳转到 /jyxxgc?type=2
        tab_url = "https://www.shggzy.com/search/queryContents.jhtml?title=&channelId=38&origin=&inDates=4000&ext=&timeBegin=&timeEnd=&ext1=&ext2=&cExt=eyJhbGciOiJIUzI1NiJ9.eyJwYXRoIjoiL2p5eHh6YyIsInBhZ2VObyI6MSwiZXhwIjoxNzU0ODI3MTcxOTI5fQ.e_db8mCQs6iFnbfOEx5MBB8ZawPZxI_EeYMPTmCzsgk"  # 替换为实际跳转的 URL
        
        yield scrapy.Request(
            tab_url,
            callback=self.parse_tab_data,  # 跳转后解析数据
            headers={'Referer': response.url}
        )

    def parse_tab_data(self, response):
        """点击选项卡后的数据解析"""
        # 2. 提取目标数据
        node_list = response.xpath('//*[@id="allList"]/ul/li')
        
        for node in node_list:
            item = ShanghaiItem()
            item['depart'] = response.xpath('normalize-space(//*[@id="content"]/div/ul/li[3]/span/text())').get('').strip()            
            item['name'] = node.xpath('.//span[@class="cs-span2"]/text()').get('').strip()
            item['link'] = response.urljoin(node.xpath('./@onclick').re_first(r"window.open\('([^']+)'\)"))
            item['number'] = node.xpath('normalize-space(.//span[contains(@style, "width: 22%")]/text())').get('')
            item['date'] = node.xpath('.//span[last()]/text()').get('').strip()

            if item['link']:
                yield scrapy.Request(
                    item['link'],
                    callback=self.parse_detail_page,
                    meta={'item': item},  # 传递已经提取的item数据
                    headers={'Referer': response.url},
                    dont_filter=True  # 避免因重复URL被过滤
                )
            else:
                yield item  # 如果没有链接，直接返回基础信息

        current_page = 1  # 默认第一页
        if 'pageNo=' in response.url:
            current_page = int(response.url.split('pageNo=')[1].split('&')[0])
    
        if current_page < self.max_page:
            next_page = current_page + 1
        # 构造下一页URL，保留原始参数并更新pageNo
            if 'pageNo=' in response.url:
                next_page_url = response.url.replace(
                    f'pageNo={current_page}', 
                    f'pageNo={next_page}'
                )
            else:
            # 如果URL中没有pageNo参数，添加它
                separator = '&' if '?' in response.url else '?'
                next_page_url = f"{response.url}{separator}pageNo={next_page}"
        
            yield scrapy.Request(
                next_page_url,
                callback=self.parse_tab_data,
                headers={'Referer': response.url}
            )

    def parse_detail_page(self, response):
        # 获取从列表页传递过来的item
        item = response.meta['item']
        
        # 提取详情页中的信息并添加到item中
        # 页面所有信息
        # item['message'] = '\n'.join(
        #     response.xpath('//div[contains(@class,"content")]//text()[normalize-space()]').getall()
        # ).strip()
        
        # 可以添加更多详情页字段的提取逻辑...
        # 例如：
        
        item['report_name'] = response.xpath('''
            normalize-space(
                //td[contains(., "采购项目名称")]/following-sibling::td[1]|
                //li[contains(., "采购项目名称")]/following-sibling::li[1]|
                //*[contains(text(), "采购项目名称")]/following::text()[1]
            )
        ''').get('').strip()
        
        # item['caigouren'] = response.xpath(
        #     'normalize-space(//td[contains(., "采购人信息")]/../td[contains(., "名 称")]/following-sibling::td)'
        # ).get()

        

        item['caigouren'] = response.xpath('''
            normalize-space(
                //*[contains(text(), "采购人信息")]/following::samp[1]|
                /*[contains(text(), "名 称")]/following::samp[1]
                )
        ''').get()

        # item['dailijigou'] = response.xpath(
        #     'normalize-space(//td[contains(., "采购代理机构名称")]/following-sibling::td)'
        # ).get('').strip()
        item['dailijigou'] = response.xpath('''
            normalize-space(
                //td[contains(., "采购代理机构名称")]/following-sibling::td[1]|
                //li[contains(., "采购代理机构名称")]/following-sibling::li[1]|
                //*[contains(text(), "采购代理机构名称")]/following::text()[1]
            )
        ''').get('').strip()

        item['xiangmudizhi'] = response.xpath('''
            normalize-space(
                //*[contains(text(), "采购人信息")]/following::samp[1]|
                /*[contains(text(), "地 址")]/following::samp[1]
                )
        ''').get()

        item['zhongbiaoren'] = response.xpath('''
            normalize-space(
                //td[contains(., "中标（成交）供应商名称")]/following-sibling::td[1]|
                //li[contains(., "中标（成交）供应商名称")]/following-sibling::li[1]|
                //*[contains(text(), "中标（成交）供应商名称")]/following::text()[1]
            )
        ''').get('').strip()



        item['zhongbiaojine'] = response.xpath('normalize-space(//td[@class="code-summaryPrice"]/text())').get('').strip()       

        item['zhongbiaoshijian'] = response.xpath('''
            normalize-space(
                //td[contains(., "首次公告时间")]/following-sibling::td[1]|
                //li[contains(., "首次公告时间")]/following-sibling::li[1]|
                //*[contains(text(), "首次公告时间")]/following::text()[1]
            )
        ''').get('').strip()

    
        

        # 返回完整的item，包含列表页和详情页的数据
        yield item