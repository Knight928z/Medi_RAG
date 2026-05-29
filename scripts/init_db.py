from core.config import get_settings
from storage.database import create_engine_from_url
from storage.models import Base


def main() -> None:
    settings = get_settings()
    engine = create_engine_from_url(settings.database_url)
    Base.metadata.create_all(engine)
    print("数据库表已初始化")


if __name__ == "__main__":
    main()
