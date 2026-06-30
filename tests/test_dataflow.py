from pathlib import Path

from test_evaluator.ingest import load_records
from test_evaluator.schemas import TestRecord as Record
from test_evaluator.static_verifier import extract_static_facts, static_review


DATASET = Path(__file__).parents[1] / "e2edev_sample.csv"


def test_req1_drag_cases_have_distinct_assertion_flows() -> None:
    records = {
        record.record_key: record
        for record in load_records(DATASET)
        if record.project_id == "E2ESD_Bench_01" and record.requirement_id == "1"
    }

    strong = extract_static_facts(records["E2ESD_Bench_01::1::1"]).data_flow
    dom_proxy = extract_static_facts(records["E2ESD_Bench_01::1::2"]).data_flow
    placeholder = extract_static_facts(records["E2ESD_Bench_01::1::3"]).data_flow
    negative_proxy = extract_static_facts(records["E2ESD_Bench_01::1::4"]).data_flow

    assert strong.event_payload_assertion_count == 3
    assert strong.data_transfer_read_keys == ["money", "title"]
    assert strong.data_transfer_set_keys == []
    assert dom_proxy.dom_assertion_count == 4
    assert dom_proxy.event_payload_assertion_count == 0
    assert placeholder.constant_assertion_count == 2
    assert placeholder.dom_assertion_count == 2
    assert negative_proxy.element_attribute_proxy_assertion_count == 1
    assert negative_proxy.constant_assertion_count == 2


def test_self_fulfilled_data_transfer_is_identified_and_flagged() -> None:
    record = Record(
        project_id="Golden",
        requirement_id="drag",
        test_id="self_fulfilled",
        requirement="The drag handler captures the title in DataTransfer.",
        scenario=(
            "Scenario: [Normal] Capture title\n"
            "  When the item is dragged\n"
            "  Then the title should be captured"
        ),
        step_code='''
from behave import when, then

@when("the item is dragged")
def drag(context):
    context.value = context.driver.execute_script("""
        const dt = new DataTransfer();
        dt.setData('title', 'Injected');
        arguments[0].dispatchEvent(new DragEvent('dragstart', {dataTransfer: dt}));
        return dt.getData('title');
    """, context.item)

@then("the title should be captured")
def title(context):
    assert context.value == "Injected"
''',
    )

    facts = extract_static_facts(record)
    review = static_review(record, facts)

    assert facts.data_flow.self_fulfilled_event_payload_assertion_count == 1
    assert any(
        finding.criterion == "Event-payload assertions observe application-produced data"
        for finding in review.findings
    )
