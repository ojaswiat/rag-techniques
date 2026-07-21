import config


def test_model_routing_has_all_stages():
    expected_stages = {"generator", "critic", "p3_index_build", "answerer", "judge", "debug"}
    assert set(config.MODEL_ROUTING.keys()) == expected_stages


def test_generator_and_critic_are_different_families():
    assert config.MODEL_ROUTING["generator"].split("/")[0] != config.MODEL_ROUTING["critic"].split("/")[0]


def test_answerer_and_judge_are_different_families():
    answerer_family = config.MODEL_ROUTING["answerer"].split("-")[0]
    judge_family = config.MODEL_ROUTING["judge"].split("/")[0]
    assert answerer_family != judge_family


def test_throttle_limit_is_three():
    assert config.THROTTLE_LIMIT == 3


def test_concurrency_cap_is_five():
    assert config.GROQ_MAX_CONCURRENCY == 5
