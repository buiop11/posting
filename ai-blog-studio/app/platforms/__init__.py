from app.platforms import naver, tistory

PLATFORMS = {
    naver.KEY: naver,
    tistory.KEY: tistory,
}

PLATFORM_LABELS = {module.KEY: module.NAME for module in PLATFORMS.values()}
