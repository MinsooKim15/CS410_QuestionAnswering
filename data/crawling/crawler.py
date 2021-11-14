import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium import webdriver
from urllib.request import urlopen
from bs4 import BeautifulSoup as bs
from urllib.parse import quote_plus
from selenium.webdriver.common.keys import Keys
import time
from selenium.common.exceptions import NoSuchElementException
from article import *
import json

# user id and password for selenium log in to campuswire

USER_ID = ""
USER_PASSWORD = ""
FILENAME = ""
CHROME_DRIVER_PATH = ""
def check_exists_by_selector(driver, xpath):
    try:
        driver.find_element_by_css_selector(xpath)
    except NoSuchElementException:
        return False
    return True



def getSubReplyList(element):
    subReplyResultList = []
    if check_exists_by_selector(element,'.post-comments-list'):
        subReplyList = element.find_element_by_class_name("post-comments-list").find_elements_by_class_name("media")
        if subReplyList != None:
            if len(subReplyList) > 0:
                for subItem in subReplyList:
                    # print("useName")
                    # print(subItem.find_element_by_class_name("user--name").find_element_by_tag_name("h6").text)
                    userName = subItem.find_element_by_class_name("user--name").find_element_by_tag_name("h6").text
                    userType = 2
                    # print("userType")
                    if check_exists_by_selector(element,'.ta-badge'):
                        userType = 1
                    if check_exists_by_selector(element,'.instructor-badge'):
                        userType = 0
                    # print("본문")
                    # print(subItem.find_element_by_class_name("text-wrapper").text)
                    content = subItem.find_element_by_class_name("text-wrapper").text
                    subReplyList = getSubReplyList(subItem)
                    reply = Reply.fromCrawl(
                        userName = userName,
                        userType = userType,
                        content = content,
                        subReplyList = subReplyList,
                        replyType = 1
                    )
                    subReplyResultList.append(reply)
    return subReplyResultList



def getPostItem(id, driver):
    # print("제목")
    # print(driver.find_element_by_tag_name("h3").text)
    #
    # print("본문")
    # print(driver.find_element_by_class_name("post-body").text)
    # # print("post-category")
    # # print(driver.find_element_by_class_name("category-5").text)
    # print("like")
    # print(driver.find_element_by_class_name("post-like").find_element_by_class_name("counter").text)
    # print("comment")
    # print(driver.find_element_by_class_name("post-comments-count").find_element_by_tag_name("span").text)
    # print("view-count")
    # print(driver.find_element_by_class_name("post-views-count").find_element_by_tag_name("span").text)
    # print("unique-view-count")
    # print(driver.find_element_by_class_name("unique-views-count-wrap").find_element_by_tag_name("span").text)

    userName = driver.find_element_by_class_name("user--name").find_element_by_tag_name("h6").text
    userType = 2
    # print("userType")
    if check_exists_by_selector(driver, '.ta-badge'):
        userType = 1
    if check_exists_by_selector(driver, '.instructor-badge'):
        userType = 0

    title = driver.find_element_by_tag_name("h3").text
    content = driver.find_element_by_class_name("post-body").text
    likeCount = driver.find_element_by_class_name("post-like").find_element_by_class_name("counter").text
    commentCount = driver.find_element_by_class_name("post-comments-count").find_element_by_tag_name("span").text
    viewCount = driver.find_element_by_class_name("post-views-count").find_element_by_tag_name("span").text
    uniqueViewCount = driver.find_element_by_class_name("unique-views-count-wrap").find_element_by_tag_name("span").text
    topAnswerList = driver.find_elements_by_class_name("top-answer")
    replyList = []
    for item in topAnswerList:
        # print("userName")
        # print(item.find_element_by_class_name("user--name").find_element_by_tag_name("h6").text)
        userName = item.find_element_by_class_name("user--name").find_element_by_tag_name("h6").text
        userType = 2
        # print("userType")
        if check_exists_by_selector(driver, '.ta-badge'):
            userType = 1
        if check_exists_by_selector(driver, '.instructor-badge'):
            userType = 0
        # print("upvote")
        # print(item.find_element_by_class_name("vote-counter").find_element_by_class_name("badge").text)
        upvote = int(item.find_element_by_class_name("vote-counter").find_element_by_class_name("badge").text)
        #
        # print("본문")
        # print(item.find_element_by_class_name("post-body").text)
        content = item.find_element_by_class_name("post-body").text
        subReplyList = getSubReplyList(item)
        reply = Reply.fromCrawl(
            userName=userName,
            userType=userType,
            content=content,
            subReplyList=subReplyList,
            replyType=0
        )
        replyList.append(reply)
    article = Article.fromCrawl(
        id = id,
        category = "post",
        userName = userName,
        userType = userType,
        content = content,
        title = title,
        inLinkId = "",
        replyList =replyList,
        likeCount = likeCount,
        commentCount = commentCount,
        viewCount = viewCount,
        uniqueViewCount=uniqueViewCount
    )
    return article

def crawl_caampuswire():
    url = 'https://campuswire.com/signin'

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(CHROME_DRIVER_PATH, chrome_options=chrome_options)
    driver.get(url)
    body = driver.find_elements_by_class_name("form-control")
    body[0].send_keys(USER_ID)
    body[1].send_keys(USER_PASSWORD)
    driver.find_element_by_class_name("btn").click()
    # driver.manage().timeouts().implicitlyWait(20, TimeUnit.SECONDS);
    time.sleep(3)
    base_url = "https://campuswire.com/c/G0A3AA370/feed/"
    articleList = []
    for i in range(4, 1350):
        url = base_url + str(i)
        driver.get(url)
        time.sleep(3)
        if check_exists_by_selector(driver, ".post-body"):
            article = getPostItem(i, driver)
            articleList.append(article)
    jsonList = []
    for article in articleList:
        jsonList.append(article.toDict())
    with open(FILENAME, 'w', encoding="utf-8") as f:
        json.dump(jsonList, f, ensure_ascii=False)

if __name__ == "__main__":
    crawl_caampuswire()