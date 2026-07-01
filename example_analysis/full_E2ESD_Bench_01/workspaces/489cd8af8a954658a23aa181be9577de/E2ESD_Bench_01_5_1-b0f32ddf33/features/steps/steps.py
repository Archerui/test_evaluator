from behave import given, when, then
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

file_path = "/home/rkr/siemens/test_evaluator/example_analysis/full_E2ESD_Bench_01/workspaces/489cd8af8a954658a23aa181be9577de/E2ESD_Bench_01_5_1-b0f32ddf33/app/index.html"

def is_visible(element):
    return element.is_displayed()

@given('the webpage is loaded with a list of products')
def step_given_webpage_loaded(context):
    context.driver = webdriver.Chrome()
    context.driver.get(f"file:///home/rkr/siemens/test_evaluator/example_analysis/full_E2ESD_Bench_01/workspaces/489cd8af8a954658a23aa181be9577de/E2ESD_Bench_01_5_1-b0f32ddf33/app/index.html")
    time.sleep(1)  # Allow time for the page to load

@when('the user drags the product with data-testid "product-item-1" to the drop area with data-testid "drop-area"')
def step_when_drag_product_to_drop_area(context):
    driver = context.driver
    product = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='product-item-1']"))
    )
    drop_area = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='drop-area']"))
    )

    # Perform drag and drop using JavaScript
    driver.execute_script("""
        function createEvent(typeOfEvent) {
            var event = document.createEvent("CustomEvent");
            event.initCustomEvent(typeOfEvent, true, true, null);
            event.dataTransfer = {
                data: {},
                setData: function(key, value) {
                    this.data[key] = value;
                },
                getData: function(key) {
                    return this.data[key];
                }
            };
            return event;
        }

        function dispatchEvent(element, event, transferData) {
            if (transferData !== undefined) {
                event.dataTransfer = transferData;
            }
            if (element.dispatchEvent) {
                element.dispatchEvent(event);
            } else if (element.fireEvent) {
                element.fireEvent("on" + event.type, event);
            }
        }

        function simulateHTML5DragAndDrop(element, target) {
            var dragStartEvent = createEvent('dragstart');
            dispatchEvent(element, dragStartEvent);
            var dropEvent = createEvent('drop');
            dispatchEvent(target, dropEvent, dragStartEvent.dataTransfer);
            var dragEndEvent = createEvent('dragend');
            dispatchEvent(element, dragEndEvent, dropEvent.dataTransfer);
        }

        var source = arguments[0];
        var target = arguments[1];
        simulateHTML5DragAndDrop(source, target);
    """, product, drop_area)
    time.sleep(1)  # Allow time for the drop action to complete

@then('the total price displayed in the element with id "allMoney" should be "$40.00"')
def step_then_verify_total_price(context):
    driver = context.driver
    total_price_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "allMoney"))
    )
    expected_price = "$40.00"
    actual_price = total_price_element.text.strip()
    assert expected_price in actual_price, f"Expected total price '{expected_price}', but got '{actual_price}'"

    # Close the browser after the test
    context.driver.quit()
