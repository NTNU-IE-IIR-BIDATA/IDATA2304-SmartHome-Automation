import logging


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    try:
        print("Control panel connected")
    except KeyboardInterrupt:
        logging.info("Control panel shut down")


if __name__ == "__main__":
    main()
