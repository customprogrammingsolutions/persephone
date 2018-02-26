""" Testing Persephone on Alex/Steven's Kunwinjku data. """

from os.path import splitext
from pathlib import Path
import subprocess
from typing import List

import pytest

from persephone import config
from persephone import utterance
from persephone.utterance import Utterance
from persephone.datasets import bkw
from persephone.preprocess import elan
from persephone.corpus_reader import CorpusReader

@pytest.mark.notravis
class TestBKW:

    tgt_dir = Path(config.TEST_TGT_DATA_ROOT) / "bkw"
    en_words_path = Path(config.EN_WORDS_PATH)
    NUM_UTTERS = 987

    @pytest.fixture(scope="class")
    def prep_org_data(self):
        """ Ensure the un-preprocessed data is available. """

        # Ensure the BKW data is all there
        bkw_path = Path(config.BKW_PATH)
        if not bkw_path.is_dir():
            raise NotImplementedError(
                "Data isn't available and I haven't figured out how authentication"
                " should best work for datasets that aren't yet public.")
        assert bkw_path.is_dir()

        # Ensure english-words/words.txt is there.
        assert self.en_words_path.is_file()

        return bkw_path

    @pytest.fixture
    def clean_tgt_dir(self):
        """ Clears the target testing directory. """

        if self.tgt_dir.is_dir():
            import shutil
            shutil.rmtree(str(self.tgt_dir))

        assert not self.tgt_dir.is_dir()

    def check_corpus(self):
        corp = bkw.Corpus(tgt_dir=self.tgt_dir)

        assert len(corp.determine_prefixes()) == self.NUM_UTTERS
        assert (self.tgt_dir / "wav").is_dir()
        assert len(list(corp.wav_dir.iterdir())) == self.NUM_UTTERS

    @pytest.mark.slow
    def test_bkw_preprocess(self, prep_org_data, clean_tgt_dir):
        self.check_corpus()

    def test_bkw_after_preprocessing(self):
        self.check_corpus()

    @staticmethod
    def count_empty(utterances: List[Utterance]) -> int:
        empty_count = 0
        for utter in utterances:
            if utter.text.strip() == "":
                empty_count += 1
        return empty_count

    def test_utterances_from_dir(self, prep_org_data):
        bkw_org_path = prep_org_data

        utterances = elan.utterances_from_dir(bkw_org_path, ["xv"])
        assert len(utterances) == 1036
        assert len(utterance.remove_empty(utterances)) == 1035
        assert len(utterance.remove_duplicates(utterances)) == 1029
        assert len(utterance.remove_duplicates(
                                   utterance.remove_empty(utterances))) == 1028

        utterances = elan.utterances_from_dir(bkw_org_path, ["rf"])
        assert len(utterances) == 1242
        assert len(utterance.remove_empty(utterances)) == 631
        assert len(utterance.remove_duplicates(utterances)) == 1239
        assert len(utterance.remove_duplicates(
                                   utterance.remove_empty(utterances))) == 631

        utterances = elan.utterances_from_dir(bkw_org_path, ["rf", "xv"])
        assert len(utterances) == 2278
        assert len(utterance.remove_empty(utterances)) == 1666
        assert len(utterance.remove_duplicates(utterances)) == 1899
        assert len(utterance.remove_duplicates(
                                   utterance.remove_empty(utterances))) == 1291

    @staticmethod
    def check_text_in_utters(text: str, utters: List[Utterance]) -> bool:
        """ Checks that the target text is found in utterances. """
        for utter in utters:
            if utter.text == text:
                return True
        return False

    def test_mark_on_rock_rf_xv_duplicate(self, prep_org_data):
        mark_on_rock_path = prep_org_data / "Mark on Rock.eaf"
        anbuyika_text = (" Anbuyika rudno karudyo mani arriwa::::m"
                         " arribebmeng Madjinbardi")

        xv_utters = elan.utterances_from_eaf(mark_on_rock_path, ["xv"])
        rf_utters = elan.utterances_from_eaf(mark_on_rock_path, ["rf"])
        xv_rf_utters = elan.utterances_from_eaf(mark_on_rock_path, ["xv", "rf"])

        assert self.check_text_in_utters(anbuyika_text, xv_utters)
        assert self.check_text_in_utters(anbuyika_text, rf_utters)
        assert self.check_text_in_utters(anbuyika_text, xv_rf_utters)
        assert not self.check_text_in_utters("some random text", xv_rf_utters)

        assert len(xv_utters) == 425
        assert len(rf_utters) == 420
        assert len(xv_rf_utters) == 845
        assert len(utterance.remove_duplicates(xv_rf_utters)) == 476
        assert len(utterance.remove_empty(
                   utterance.remove_duplicates(xv_rf_utters))) == 473

    def test_corpus_duration(self, prep_org_data):
        corp = bkw.Corpus(tgt_dir=self.tgt_dir)
        cr = CorpusReader(corp)
        cr.calc_time()

    def test_explore_code_switching(self, prep_org_data):
        bkw_org_path = prep_org_data
        utterances = elan.utterances_from_dir(bkw_org_path, ["rf", "xv"])
        utterances = utterance.remove_empty(
                     utterance.remove_duplicates(utterances))
        codeswitched_path = self.tgt_dir / "codeswitched.txt"
        bkw.explore_code_switching(utterances, codeswitched_path)

    def test_speaker_id(self, prep_org_data):
        bkw_org_path = prep_org_data
        utterances = elan.utterances_from_dir(bkw_org_path, ["rf", "xv"])
        no_speaker_tiers = set()
        speaker_tiers = set()
        speakers = set()
        for utter in utterances:
            tier_id = splitext(utter.prefix)[0]
            if utter.participant == None:
                no_speaker_tiers.add(tier_id)
            else:
                speaker_tiers.add((tier_id, utter.participant))
                speakers.add(utter.participant)

        assert len(no_speaker_tiers) == 0

        print(speakers)
        print(len(speakers))
