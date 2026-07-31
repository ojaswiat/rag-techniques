import config

def test_model_routing_has_all_stages():
    expected_stages = {"generator", "critic", "p3_index_build", "answerer", "judge", "debug"}
    assert set(config.MODEL_ROUTING.keys()) == expected_stages

def test_generator_and_critic_are_different_families():
    gen = config.MODEL_ROUTING["generator"]
    crit = config.MODEL_ROUTING["critic"]
    # Each entry is dict with model and provider
    gen_family = gen["model"].split("/")[0] if isinstance(gen, dict) else gen.split("/")[0]
    crit_family = crit["model"].split("/")[0] if isinstance(crit, dict) else crit.split("/")[0]
    assert gen_family != crit_family

def test_answerer_and_judge_are_different_families():
    answerer = config.MODEL_ROUTING["answerer"]
    judge = config.MODEL_ROUTING["judge"]
    answerer_family = answerer["model"].split("-")[0] if isinstance(answerer, dict) else answerer.split("-")[0]
    judge_family = judge["model"].split("/")[0] if isinstance(judge, dict) else judge.split("/")[0]
    assert answerer_family != judge_family

def test_throttle_limit_is_three():
    assert config.THROTTLE_LIMIT == 3

def test_concurrency_cap_is_five():
    assert config.GROQ_MAX_CONCURRENCY == 5
