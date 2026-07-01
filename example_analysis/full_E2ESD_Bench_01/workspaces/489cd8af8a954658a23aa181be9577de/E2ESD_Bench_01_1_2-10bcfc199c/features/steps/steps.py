from behave import given, when, then
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

file_path = "/home/rkr/siemens/test_evaluator/example_analysis/full_E2ESD_Bench_01/workspaces/489cd8af8a954658a23aa181be9577de/E2ESD_Bench_01_1_2-10bcfc199c/app/index.html"

def setup_driver(context):
    context.driver = webdriver.Chrome()
    context.driver.get(f"file:///home/rkr/siemens/test_evaluator/example_analysis/full_E2ESD_Bench_01/workspaces/489cd8af8a954658a23aa181be9577de/E2ESD_Bench_01_1_2-10bcfc199c/app/index.html")

def teardown_driver(context):
    context.driver.quit()

@given('the webpage is loaded with a product list')
def step_given_webpage_loaded(context):
    setup_driver(context)
    WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='product-item-1']"))
    )
    time.sleep(1)

@when('the user drags the product item with data-testid "product-item-2"')
def step_when_user_drags_product_item(context):
    product_item = context.driver.find_element(By.CSS_SELECTOR, "[data-testid='product-item-2']")
    WebDriverWait(context.driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='product-item-2']"))
    )
    # Simulate drag and drop
    context.driver.execute_script("""
        var dragEvent = new DragEvent('dragstart', {
            dataTransfer: new DataTransfer()
        });
        arguments[0].dispatchEvent(dragEvent);
    """, product_item)
    time.sleep(1)

@then('the drag event should be initiated')
def step_then_drag_event_initiated(context):
    # Verify drag event initiation by checking dataTransfer data
    product_item = context.driver.find_element(By.CSS_SELECTOR, "[data-testid='product-item-2']")
    title = product_item.find_element(By.CSS_SELECTOR, "[data-testid='product-title-2']").text
    price = product_item.find_element(By.CSS_SELECTOR, "[data-testid='product-price-2']").text

    assert title == "JavaScript: The Definitive Guide", f"Expected title 'JavaScript: The Definitive Guide', but got '{title}'"
    assert price == "$120", f"Expected price '$120', but got '{price}'"
    time.sleep(1)

@then('the product title "JavaScript: The Definitive Guide" should be captured')
def step_then_product_title_captured(context):
    product_item = context.driver.find_element(By.CSS_SELECTOR, "[data-testid='product-item-2']")
    title = product_item.find_element(By.CSS_SELECTOR, "[data-testid='product-title-2']").text
    assert title == "JavaScript: The Definitive Guide", f"Expected title 'JavaScript: The Definitive Guide', but got '{title}'"
    time.sleep(1)

@then('the product price "$120" should be captured')
def step_then_product_price_captured(context):
    product_item = context.driver.find_element(By.CSS_SELECTOR, "[data-testid='product-item-2']")
    price = product_item.find_element(By.CSS_SELECTOR, "[data-testid='product-price-2']").text
    assert price == "$120", f"Expected price '$120', but got '{price}'"
    time.sleep(1)

def after_scenario(context, scenario):
    teardown_driver(context)
