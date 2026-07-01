from behave import given, when, then
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

file_path = "/home/rkr/siemens/test_evaluator/example_analysis/full_E2ESD_Bench_01/workspaces/489cd8af8a954658a23aa181be9577de/E2ESD_Bench_01_5_3-cd1576b12d/app/index.html"

def is_expanded(element):
    aria = element.get_attribute("aria-expanded")
    if aria is not None:
        return aria == "true"

    class_list = element.get_attribute("class").split()
    if any(cls in class_list for cls in ["expanded", "open", "show"]):
        return True

    data_expanded = element.get_attribute("data-expanded")
    if data_expanded is not None:
        return data_expanded == "true"

    return element.is_displayed()

def is_collapsed(element):
    aria = element.get_attribute("aria-expanded")
    if aria is not None and aria.lower() == "false":
        return True

    class_attr = element.get_attribute("class") or ""
    class_list = class_attr.split()
    if "collapsed" in class_list:
        return True

    data_expanded = element.get_attribute("data-expanded")
    if data_expanded is not None and data_expanded.lower() == "false":
        return True

    style = element.get_attribute("style") or ""
    if "display: none" in style or "visibility: hidden" in style or "height: 0" in style:
        return True

    return not element.is_displayed()

@given('the webpage is loaded with a list of products')
def step_given_webpage_loaded(context):
    context.driver = webdriver.Chrome()
    context.driver.get(f"file:///home/rkr/siemens/test_evaluator/example_analysis/full_E2ESD_Bench_01/workspaces/489cd8af8a954658a23aa181be9577de/E2ESD_Bench_01_5_3-cd1576b12d/app/index.html")
    time.sleep(1)

@when('the user drags the product with data-testid "{product_testid}" to the drop area with data-testid "{drop_area_testid}"')
def step_when_drag_product_to_drop_area(context, product_testid, drop_area_testid):
    product = WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='{product_testid}']"))
    )
    drop_area = WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='{drop_area_testid}']"))
    )
    
    # Simulate drag and drop
    context.driver.execute_script("""
        var product = arguments[0];
        var dropArea = arguments[1];
        var dataTransfer = new DataTransfer();
        product.dispatchEvent(new DragEvent('dragstart', {dataTransfer: dataTransfer}));
        dropArea.dispatchEvent(new DragEvent('drop', {dataTransfer: dataTransfer}));
    """, product, drop_area)
    time.sleep(1)

@then('the total price displayed in the element with id "{total_price_id}" should be "{expected_price}"')
def step_then_verify_total_price(context, total_price_id, expected_price):
    total_price_element = WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located((By.ID, total_price_id))
    )
    actual_price = total_price_element.text.strip()
    assert expected_price in actual_price, f"Expected price '{expected_price}', but got '{actual_price}'"
    time.sleep(1)

def after_scenario(context, scenario):
    context.driver.quit()
