from config import config
from utils import import_csv_questions

IMPORT_CSV_FILENAMES = [
                        f"{config['BASE_DIR']}data/import/buzzwords_1.csv",
                        f"{config['BASE_DIR']}data/import/buzzwords_2.csv",
                        f"{config['BASE_DIR']}data/import/buzzwords_3.csv",
                        f"{config['BASE_DIR']}data/import/buzzwords_4.csv",
                        f"{config['BASE_DIR']}data/import/buzzwords_5.csv",
                        f"{config['BASE_DIR']}data/import/malware_1.csv",
                        f"{config['BASE_DIR']}data/import/malware_2.csv",
                        f"{config['BASE_DIR']}data/import/malware_3.csv",
                        f"{config['BASE_DIR']}data/import/malware_4.csv",
                        f"{config['BASE_DIR']}data/import/malware_5.csv",
                        f"{config['BASE_DIR']}data/import/infosec_1.csv",
                        f"{config['BASE_DIR']}data/import/infosec_2.csv",
                        f"{config['BASE_DIR']}data/import/infosec_3.csv",
                        f"{config['BASE_DIR']}data/import/infosec_4.csv",
                        f"{config['BASE_DIR']}data/import/infosec_5.csv",
                        f"{config['BASE_DIR']}data/import/redguard_1.csv",
                        f"{config['BASE_DIR']}data/import/redguard_2.csv",
                        f"{config['BASE_DIR']}data/import/redguard_3.csv",
                        f"{config['BASE_DIR']}data/import/redguard_4.csv",
                        f"{config['BASE_DIR']}data/import/redguard_5.csv",
                        f"{config['BASE_DIR']}data/import/hacker_on_tv_1.csv",
                        f"{config['BASE_DIR']}data/import/hacker_on_tv_2.csv",
                        f"{config['BASE_DIR']}data/import/hacker_on_tv_3.csv",
                        f"{config['BASE_DIR']}data/import/hacker_on_tv_4.csv",
                        f"{config['BASE_DIR']}data/import/hacker_on_tv_5.csv",
                        ]
IMPORT_CATEGORY_NAMES = ["Buzzwords I", "Buzzwords II", "Buzzwords III", "Buzzwords IV", "Buzzwords V",
                         "Malware I", "Malware II", "Malware III", "Malware IV", "Malware V",
                         "Infosec I", "Infosec II", "Infosec III", "Infosec IV", "Infosec V",
                         "Redguard I", "Redguard II", "Redguard III", "Redguard IV", "Redguard V",
                         "Hacker im TV I", "Hacker im TV II", "Hacker im TV III", "Hacker im TV IV", "Hacker im TV V",
                         ]


def main() -> None:
    import_csv_questions(IMPORT_CSV_FILENAMES, IMPORT_CATEGORY_NAMES)


if __name__ == "__main__":
    main()
