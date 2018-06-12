import re

import scrapy
import json
from scrapy import Request
from haodai.items import loanItem
from scrapy_redis.spiders import RedisCrawlSpider


class DiscoverySpider(scrapy.Spider):
    name = 'haodai'
    # allowed_domains = ['www.haodai.com']
    start_urls = ['http://www.haodai.com/loan/']

    # 提取作者的著作权信息
    # composer_url = 'http://www.xinpianchang.com/u%s?from=articleList'

    # 获取每个地方的贷款链接
    def parse(self, response):
        # 将地方链接分别放入列表中
        url_list = response.xpath("//div[@id='city_box']/dl/dd/a/@href").extract()
        # 贷款时间与贷款金额
        times = [3, 6, 12, 18, 24, 36]
        moneys = [5, 10, 15, 20, 25, 30]
        # 得到每个贷款链接
        for url in url_list:
            for money in moneys:
                for time in times:
                    pace_url = url + '/s4-%dx%d-0x0x9999/' % (money, time)
                    yield response.follow(pace_url, meta={'url': url}, callback=self.parse_post)

    # 处理每个地方的代理页
    def parse_post(self, response):
        lists = response.xpath('//div[@class="ma_nr"]')
        # # 获取各各地方具体的贷款链接
        for list in lists:
            # 获取贷款公司的 id号 x 贷款金额 x 时间
            url = list.xpath(".//span/a/@href").extract_first()
            conpany_id = re.findall("/(\d+x\d+x\d+?)\.", url)[0]
            # 获取列表也的公司图片链接
            company_img = response.meta['url'] + list.xpath(".//span/a/img/@src").extract_first()
            # 贷款方式
            load_method = list.xpath(".//p[@class='jqtap co9']/a/@title").extract_first()
            # 星级评价
            evaluation = list.xpath(".//samp/p[@class='Pstars']/span/em/@class").extract_first()
            # 贷款人要求
            lr = list.xpath(".//div[@class='con04']/p/text()").extract()
            lender_requirements = ";".join(lr)
            # 产品特点
            f1 = list.xpath(".//ul[@class='icon']/li/a/@title").extract()
            features = ";".join(f1)
            # 产品特点图片
            f2 = list.xpath(".//ul[@class='icon']/li/a/@style").extract()
            fea = ";".join(f2)
            f3 = re.findall("\'(.*?)\'", fea)
            features_img = ""
            for imgurl in f3:
                features_img += response.meta['url'] + imgurl + ";"
            print(features_img)
            # print(conpany_id,company_img,load_method,evaluation,lender_requirements,features,features_img)
            # # 进入详情页继续访问
            request = Request(url, callback=self.parse_company)
            request.meta['cid'] = conpany_id
            request.meta['company_img'] = company_img
            request.meta['load_method'] = load_method
            request.meta['evaluation'] = evaluation
            request.meta['lender_requirements'] = lender_requirements
            request.meta['features'] = features
            request.meta['features_img'] = features_img
            yield request



    # 公司具体贷款信息
    def parse_company(self, response):

        # 获取items表信息
        Company = loanItem()
        # 公司id(表的主键)
        Company['cid'] = response.meta['cid']
        # 网站url
        Company['url'] = response.url
        # 获取公司名称
        Company['company_name'] = response.xpath("//span[@class='cpsp1']/text()").extract_first()
        content1 = response.xpath("//td[@class='cptd2']/text()").extract()
        # 金额(单位万)
        money = re.findall('\d+', content1[0])[0]
        Company['money'] = int(money)
        # 期限(月)
        limit_time = re.findall('\d+', content1[1])[0]
        Company['limit_time'] = int(limit_time)
        # 月供(元)
        month_supply = re.findall('\d+', content1[2])[0]
        Company['month_supply'] = int(month_supply)
        # 总费用(万)
        total_post = re.findall('(.*?)万元', content1[3])[0]
        Company['total_post'] = float(total_post)
        # 费用说明
        ls = response.xpath("//td[@class='cptd2']//span/text()").extract()
        Company['expense_description'] = " ".join(ls[1:])
        content2 = response.xpath("//td[@class='cptd4']/text()").extract()
        # 额度范围
        Company['limit_range'] = content2[0]
        # 期限范围
        Company['term_range'] = content2[1]
        # 还款方式
        Company['Repayment'] = content2[2]
        # 放款时间(天)
        loan_time = re.findall('(\d+)', content2[3])[0]
        Company['loan_time'] = int(loan_time)
        # 申请成功人
        number = response.xpath("//div[@class='success_sqrs']/span/text()").extract_first()
        Company['applicant'] = str(number)
        # print(money,limit_time,month_supply,total_post,expense_description,limit_range,term_range,Repayment,loan_time)
        content3 = response.xpath("//div[@class='kuai']/p[2]")
        # 申请条件
        li1 = content3[0].xpath('./text()').extract()
        Company['application_condition'] = " ".join(li1)
        # 所需材料
        li2 = content3[1].xpath('./text()').extract()
        Company['material'] = " ".join(li2)
        # 详细说明
        li3 = content3[2].xpath('./text()').extract()
        Company['detailed_description'] = " ".join(li3)
        # 公司图标
        Company['company_img'] = response.meta['company_img']
        # 贷款方式
        Company['load_method'] = response.meta['load_method']
        # 星级评价
        Company['evaluation'] = response.meta['evaluation']
        # 贷款要求
        Company['lender_requirements'] = response.meta['lender_requirements']
        # 公司特色
        Company['features'] = response.meta['features']
        # 公司特色图片
        Company['features_img'] = response.meta['features_img']
        # 将爬取的信息放入管道
        yield Company





