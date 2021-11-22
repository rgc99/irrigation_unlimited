import json
import re


@service("irrigation_unlimited.list_config")
def irrigation_unlimited_list_config(entity_id, section, first=None):
    """yaml
    name: List configuration
    description: Load up an input_select entity with Irrigation Unlimited config data
    fields:
      entity_id:
        description: An entity from the input_select domain
        example: input_select.irrigation_unlimited_entities
        required: true
        selector:
          entity:
            domain: input_select

      section:
        description: The type of list to load up
        example: entities
        required: true
        selector:
          select:
            options:
              - entities
              - sequences

      first:
        description: The first item in the list
        example: <select one>
        required: false
        selector:
          text:"""
    if entity_id is not None and entity_id.split(".")[0] == "input_select":
        options = []
        if first is not None:
            options.append(first)
        data = json.loads(irrigation_unlimited.coordinator.configuration)
        if section == "entities":
            for controller in data.get("controllers"):
                options.append(f"{controller['index'] + 1}.0 {controller['name']}")
                for zone in controller["zones"]:
                    options.append(
                        f"{controller['index'] + 1}.{zone['index'] + 1} {zone['name']}"
                    )
        elif section == "sequences":
            for controller in data.get("controllers"):
                for sequence in controller["sequences"]:
                    options.append(
                        f"{controller['index'] + 1}.{sequence['index'] + 1} {sequence['name']}"
                    )
        else:
            log.warning("section not found")
        input_select.set_options(entity_id=entity_id, options=options)
    else:
        log.warning("invalid entity_id")


def convert_iu_entity(entity_id) -> str:
    if entity_id is not None:
        l = re.split(r"^(\d+)\.(\d+)\s(.*)$", state.get(entity_id))
        if len(l) == 5:
            if l[2] == "0":
                l[2] = "m"
            else:
                l[2] = "z" + l[2]
            return f"binary_sensor.irrigation_unlimited_c{l[1]}_{l[2]}"
    return None


def convert_iu_sequence(entity_id) -> list:
    if entity_id is not None:
        l = re.split(r"^(\d+)\.(\d+)\s(.*)$", state.get(entity_id))
        if len(l) == 5:
            return f"binary_sensor.irrigation_unlimited_c{l[1]}_m", l[2]
    return None


@service("irrigation_unlimited.shim_manual_run")
def irrigation_unlimited_call_manual_run(
    time_entity, controller_zone_entity=None, controller_sequence_entity=None
):
    """yaml
    name: Manual run shim
    description: Decode the arguments and run the Irrigation Unlimited manual_run service
    fields:
      time_entity:
        description: An entity whose state contains the time information
        example: input_datetime.irrigation_unlimited_time
        required: true
        selector:
          time:

      controller_zone_entity:
        description: An entity whose state contains the encoded controller/zone information
        example: input_select.irrigation_unlimited_entities
        required: false
        selector:
          entity:
            domain: input_select

      controller_sequence_entity:
        description: An entity whose state contains the encoded controller/sequence information
        example: input_select.irrigation_unlimited_sequences
        required: false
        selector:
          entity:
            domain: input_select"""
    sequence_id = None
    entity_id = convert_iu_entity(controller_zone_entity)
    l = convert_iu_sequence(controller_sequence_entity)
    if l is not None:
        entity_id = l[0]
        sequence_id = l[1]
    time = state.get(time_entity)
    if entity_id is not None:
        if sequence_id is None:
            irrigation_unlimited.manual_run(entity_id=entity_id, time=time)
        else:
            irrigation_unlimited.manual_run(
                entity_id=entity_id, time=time, sequence_id=sequence_id
            )
    else:
        log.warning("invalid entity_id")


@service("irrigation_unlimited.shim_cancel")
def irrigation_unlimited_call_cancel(controller_zone_entity):
    """yaml
    name: Cancel shim
    description: Decode the arguments and run the Irrigation Unlimited cancel service
    fields:
      controller_zone_entity:
        description: An entity whose state contains the encoded controller/zone information
        example: input_select.irrigation_unlimited_entities
        required: true
        selector:
          entity:
            domain: input_select"""
    entity_id = convert_iu_entity(controller_zone_entity)
    if entity_id is not None:
        irrigation_unlimited.cancel(entity_id=entity_id)
    else:
        log.warning("invalid entity_id")


@service("irrigation_unlimited.shim_enable")
def irrigation_unlimited_call_enable(controller_zone_entity):
    """yaml
    name: Enable shim
    description: Decode the arguments and run the Irrigation Unlimited enable service
    fields:
      controller_zone_entity:
        description: An entity whose state contains the encoded controller/zone information
        example: input_select.irrigation_unlimited_entities
        required: true
        selector:
          entity:
            domain: input_select"""
    entity_id = convert_iu_entity(controller_zone_entity)
    if entity_id is not None:
        irrigation_unlimited.enable(entity_id=entity_id)
    else:
        log.warning("invalid entity_id")


@service("irrigation_unlimited.shim_disable")
def irrigation_unlimited_call_disable(controller_zone_entity):
    """yaml
    name: Disable shim
    description: Decode the arguments and run the Irrigation Unlimited disable service
    fields:
      controller_zone_entity:
        description: An entity whose state contains the encoded controller/zone information
        example: input_select.irrigation_unlimited_entities
        required: true
        selector:
          entity:
            domain: input_select"""
    entity_id = convert_iu_entity(controller_zone_entity)
    if entity_id is not None:
        irrigation_unlimited.disable(entity_id=entity_id)
    else:
        log.warning("invalid entity_id")


@service("irrigation_unlimited.shim_toggle")
def irrigation_unlimited_call_toggle(controller_zone_entity):
    """yaml
    name: Toggle shim
    description: Decode the arguments and run the Irrigation Unlimited toggle service
    fields:
      controller_zone_entity:
        description: An entity whose state contains the encoded controller/zone information
        example: input_select.irrigation_unlimited_entities
        required: true
        selector:
          entity:
            domain: input_select"""
    entity_id = convert_iu_entity(controller_zone_entity)
    if entity_id is not None:
        irrigation_unlimited.toggle(entity_id=entity_id)
    else:
        log.warning("invalid entity_id")
