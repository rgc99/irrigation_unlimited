"""irrigation_unlimited user data test"""
import homeassistant.core as ha
from tests.iu_test_support import IUExam

IUExam.quiet_mode()


async def test_user(hass: ha.HomeAssistant, skip_dependencies, skip_history):
    """Test IUUser class."""
    # pylint: disable=unused-argument

    # Start an examination
    async with IUExam(hass, "test_user.yaml") as exam:
        await exam.begin_test(1)
        attr = hass.states.get("binary_sensor.irrigation_unlimited_c1_m").attributes
        assert attr["user_area"] == "My Farm"
        assert attr["user_picture"] == "/my_pic.jpg"
        attr = hass.states.get("binary_sensor.irrigation_unlimited_c1_z1").attributes
        assert attr["user_area"] == "Eastern Pastures"
        assert attr["user_actuator"] == "KNX 6.1"
        assert attr["user_flow_rate_gallon_per_minute"] == 25
        assert attr["user_picture"] == "/my_pic.jpg"
        assert attr["user_gps"] == "42.746635,-75.770045"
        await exam.finish_test()

        exam.check_summary()
