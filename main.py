from quantresearch import __version__
from quantresearch.logger import get_logger


logger = get_logger("QuantResearch")


def main():

    logger.info("=" * 50)
    logger.info("QuantResearch v%s", __version__)
    logger.info(
        "Institution-grade Quantitative Research Platform"
    )
    logger.info(
        "Environment initialized successfully"
    )
    logger.info("=" * 50)


if __name__ == "__main__":
    main()