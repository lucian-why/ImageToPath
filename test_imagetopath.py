import os
import tempfile
import unittest
from datetime import datetime
from unittest import mock

import AppConfig
from AppConfig import AppConfig as Config
from ClipboardHelper import _build_hdrop_data
from ClipboardMonitor import ClipboardMonitor
from Program import apply_save_folder, mark_welcome_shown
from ScreenshotCapture import generate_filename


class ConfigTests(unittest.TestCase):
    def test_config_path_uses_existing_appconfig_json(self):
        self.assertEqual(os.path.basename(AppConfig.CONFIG_PATH), "AppConfig.json")

    def test_config_shows_welcome_on_first_run_by_default(self):
        self.assertTrue(Config().show_welcome_on_startup)

    def test_mark_welcome_shown_disables_future_welcome(self):
        config = Config(show_welcome_on_startup=True)

        with mock.patch("Program.save_config", return_value=True):
            self.assertTrue(mark_welcome_shown(config))

        self.assertFalse(config.show_welcome_on_startup)


class SaveFolderTests(unittest.TestCase):
    def test_apply_save_folder_does_not_change_config_when_directory_creation_fails(self):
        config = Config(save_folder=r"C:\old")

        with mock.patch("Program.os.makedirs", side_effect=OSError("denied")):
            ok, message = apply_save_folder(config, r"C:\new")

        self.assertFalse(ok)
        self.assertIn("denied", message)
        self.assertEqual(config.save_folder, r"C:\old")

    def test_apply_save_folder_changes_config_after_directory_created_and_saved(self):
        config = Config(save_folder=r"C:\old")

        with tempfile.TemporaryDirectory() as folder:
            with mock.patch("Program.save_config", return_value=True):
                ok, message = apply_save_folder(config, folder)

        self.assertTrue(ok)
        self.assertEqual(message, folder)
        self.assertEqual(config.save_folder, folder)


class ClipboardMonitorTests(unittest.TestCase):
    def test_failed_save_does_not_mark_image_hash_processed(self):
        monitor = ClipboardMonitor(Config(), on_error=lambda msg: None)
        image = mock.Mock()
        image.save.side_effect = lambda buf, format: buf.write(b"image-bytes")

        with mock.patch("ClipboardMonitor.contains_image", return_value=True), \
             mock.patch("ClipboardMonitor.get_image", return_value=image), \
             mock.patch("ClipboardMonitor.save_image", return_value=None):
            monitor._check_clipboard()

        self.assertEqual(monitor._last_image_hash, "")

    def test_failed_copy_does_not_mark_image_hash_processed(self):
        monitor = ClipboardMonitor(Config(copy_path_to_clipboard=True), on_error=lambda msg: None)
        image = mock.Mock()
        image.save.side_effect = lambda buf, format: buf.write(b"image-bytes")

        with mock.patch("ClipboardMonitor.contains_image", return_value=True), \
             mock.patch("ClipboardMonitor.get_image", return_value=image), \
             mock.patch("ClipboardMonitor.save_image", return_value=r"C:\img.png"), \
             mock.patch("ClipboardMonitor.copy_file_path", return_value=False):
            monitor._check_clipboard()

        self.assertEqual(monitor._last_image_hash, "")


class ClipboardHelperTests(unittest.TestCase):
    def test_build_hdrop_data_uses_unicode_dropfiles_format(self):
        data = _build_hdrop_data(r"C:\tmp\a.png")

        self.assertEqual(data[:4], (20).to_bytes(4, "little"))
        self.assertEqual(data[16:20], (1).to_bytes(4, "little"))
        self.assertTrue(data.endswith(b"\x00\x00\x00\x00"))
        self.assertIn(r"C:\tmp\a.png".encode("utf-16le"), data)


class FilenameTests(unittest.TestCase):
    def test_generate_filename_uses_compact_timestamp_only(self):
        config = Config(
            file_name_format="{yyyy}{MM}{dd}_{HH}{mm}{ss}",
            image_format="png",
        )

        with mock.patch("ScreenshotCapture.datetime") as fake_datetime:
            fake_datetime.now.return_value = datetime(2026, 5, 1, 18, 42, 33)

            filename = generate_filename(config, source="clipboard")

        self.assertEqual(filename, "20260501_184233.png")

    def test_save_image_adds_suffix_when_timestamp_name_exists(self):
        from PIL import Image
        from ScreenshotCapture import save_image

        config = Config(
            save_folder="",
            file_name_format="{yyyy}{MM}{dd}_{HH}{mm}{ss}",
            image_format="png",
        )
        image = Image.new("RGB", (2, 2), (255, 0, 0))

        with tempfile.TemporaryDirectory() as folder, \
             mock.patch("ScreenshotCapture.datetime") as fake_datetime:
            config.save_folder = folder
            fake_datetime.now.return_value = datetime(2026, 5, 1, 18, 42, 33)
            first = save_image(image, config)
            second = save_image(image, config)

        self.assertTrue(first.endswith("20260501_184233.png"))
        self.assertTrue(second.endswith("20260501_184233_2.png"))


if __name__ == "__main__":
    unittest.main()
