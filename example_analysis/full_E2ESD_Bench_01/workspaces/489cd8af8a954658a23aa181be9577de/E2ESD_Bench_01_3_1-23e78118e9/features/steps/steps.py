from behave import given, when, then
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

file_path = "/home/rkr/siemens/test_evaluator/example_analysis/full_E2ESD_Bench_01/workspaces/489cd8af8a954658a23aa181be9577de/E2ESD_Bench_01_3_1-23e78118e9/app/index.html"

def is_visible(element):
    return element.is_displayed()

def drag_and_drop_html5(driver, source, target):
    driver.execute_script("""
        function triggerDragAndDrop(source, target) {
            const dataTransfer = new DataTransfer();
            const dragStartEvent = new DragEvent('dragstart', { dataTransfer });
            source.dispatchEvent(dragStartEvent);

            const dragEnterEvent = new DragEvent('dragenter', { dataTransfer });
            target.dispatchEvent(dragEnterEvent);

            const dragOverEvent = new DragEvent('dragover', { dataTransfer });
            target.dispatchEvent(dragOverEvent);

            const dropEvent = new DragEvent('drop', { dataTransfer });
            target.dispatchEvent(dropEvent);

            const dragEndEvent = new DragEvent('dragend', { dataTransfer });
            source.dispatchEvent(dragEndEvent);
        }
        triggerDragAndDrop(arguments[0], arguments[1]);
    """, source, target)

@given('the webpage is loaded')
def step_given_webpage_loaded(context):
    context.driver = webdriver.Chrome()
    context.driver.get(f"file:///home/rkr/siemens/test_evaluator/example_analysis/full_E2ESD_Bench_01/workspaces/489cd8af8a954658a23aa181be9577de/E2ESD_Bench_01_3_1-23e78118e9/app/index.html")
    time.sleep(1)

@given('the product item with data-testid "{data_testid}" is visible')
def step_given_product_item_visible(context, data_testid):
    product_item = WebDriverWait(context.driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='{data_testid}']"))
    )
    assert is_visible(product_item), f"Product item with data-testid '{data_testid}' is not visible"
    time.sleep(1)

@when('the user drags the product with data-testid "product-item-1" and drops it into the cart container with data-testid "drop-area"')
def step_when_user_drags_and_drops_product(context):
    product = context.driver.find_element(By.CSS_SELECTOR, f"[data-testid='product-item-1']")
    cart_container = context.driver.find_element(By.CSS_SELECTOR, f"[data-testid='drop-area']")
    drag_and_drop_html5(context.driver, product, cart_container)
    time.sleep(1)

@then('the cart display should show a product with title "{expected_title}"')
def step_then_cart_display_shows_product_title(context, expected_title):
    cart_items = context.driver.find_elements(By.CSS_SELECTOR, "#div1 .box2")
    titles = [item.text for item in cart_items]
    assert any(expected_title in title for title in titles), f"Expected title '{expected_title}' not found in cart display"
    time.sleep(1)

@then('the price "{expected_price}"')
def step_then_cart_display_shows_price(context, expected_price):
    cart_prices = context.driver.find_elements(By.CSS_SELECTOR, "#div1 .box3")
    prices = [price.text for price in cart_prices]
    assert any(expected_price in price for price in prices), f"Expected price '{expected_price}' not found in cart display"
    time.sleep(1)

@then('the quantity "{expected_quantity}"')
def step_then_cart_display_shows_quantity(context, expected_quantity):
    cart_quantities = context.driver.find_elements(By.CSS_SELECTOR, "#div1 .box1")
    quantities = [quantity.text for quantity in cart_quantities]
    assert any(expected_quantity in quantity for quantity in quantities), f"Expected quantity '{expected_quantity}' not found in cart display"
    time.sleep(1)

def after_scenario(context, scenario):
    context.driver.quit()
