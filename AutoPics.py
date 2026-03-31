import os
import sys
import tempfile
from multiprocessing import freeze_support
from pathlib import Path
from shutil import rmtree
from typing import Any, final, override

from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QObject,
    QPropertyAnimation,
    QRunnable,
    Qt,
    QThreadPool,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import QColor, QEnterEvent, QImage, QPalette, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QTextEdit,
    QWidget,
)

from picComp import PicComp


@final
class WorkerSignals(QObject):
    finished = Signal()


# --- Background worker using QRunnable ---
@final
class LongTaskWorker(QRunnable):
    def __init__(
        self,
        source_folder: Path,
        comp_folder: Path,
        encoder: str,
        rename: str,
        disable_resize: bool,
        image_quality: str | None,
        custom_resize_px: int,
        custom_resize_bool: bool | None,
        contrast_chbx_var: bool,
        sharpen_chbx_var: bool,
        dic_standards: dict[str, str],
        trim_chbx_value: bool,
        source_images: list[str],
        ensure_standards_chbx_var: bool,
    ):
        super().__init__()

        self.source_folder = source_folder
        self.comp_folder = comp_folder
        self.encoder = encoder
        self.rename = rename
        self.disable_resize = disable_resize
        self.image_quality = image_quality
        self.custom_resize_px = custom_resize_px
        self.custom_resize_bool = custom_resize_bool
        self.contrast_chbx_var = contrast_chbx_var
        self.sharpen_chbx_var = sharpen_chbx_var
        self.dic_standards = dic_standards
        self.trim_chbx_value = trim_chbx_value
        self.source_images = source_images
        self.ensure_standards_chbx_var = ensure_standards_chbx_var

        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        # Simulate a long-running process
        print("Starting process_pics...")
        pic_comp_processor = PicComp(
            self.source_folder,
            self.comp_folder,
            self.encoder,
            self.rename,
            self.disable_resize,
            self.image_quality,
            self.custom_resize_px,
            self.custom_resize_bool,
            self.contrast_chbx_var,
            self.sharpen_chbx_var,
            self.dic_standards,
            self.trim_chbx_value,
            self.source_images,
            self.ensure_standards_chbx_var,
        )
        pic_comp_processor.process_pics()
        print("process_pics done.")
        self.signals.finished.emit()


@final
class MainWindow(QMainWindow):
    MIN_IMAGE_WIDTH = 550
    SUFFIXES = (
        "(*.jpg *.jpeg *.png *.tif *.webp *.bmp *.ico *.psd *.avif *.tiff *.jxl *.jfif)"
    )

    def __init__(self):
        super().__init__()
        self.extensions: list[str] = ["*.jpg", "*.avif", "*.jxl", "*.png"]

        self._base_window_opacity: float = 0.85
        self._changed_window_opacity: float = 1
        self._opacity_duration: int = 250
        self._opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self._opacity_animation.setDuration(self._opacity_duration)
        self._opacity_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.set_icons()

        self.threadpool = QThreadPool()

        self.app_layout = QGridLayout()
        self.app_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.create_main_window()
        self.colour_main_window()

        self.create_processing_frame()
        self.create_settings_frame()
        self.create_results_frame()
        self.create_image_frame()

        self.setCentralWidget(self.main_widget)
        self.create_app_grid_layout()

        self.set_window_size(self.MIN_IMAGE_WIDTH, 900)

    def set_icons(self):
        ico_icon = QPixmap(self.resource_path("AutoPicsIcon.ico"))
        self.setWindowIcon(ico_icon)

    def _animate_opacity(self, target: float) -> None:
        self._opacity_animation.stop()
        self._opacity_animation.setStartValue(self.windowOpacity())
        self._opacity_animation.setEndValue(target)
        self._opacity_animation.start()

    def create_main_window(self) -> None:
        self.main_widget = QWidget()
        self.setWindowOpacity(self._base_window_opacity)

        self.setWindowTitle("AutoPics - Open-Source Edition v3.0.0")

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        self._animate_opacity(self._changed_window_opacity)
        super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent, /) -> None:
        self._animate_opacity(self._base_window_opacity)
        super().leaveEvent(event)

    def create_processing_frame(self) -> None:
        processing_frame = QWidget()
        processing_frame_layout = QGridLayout()
        processing_frame.setLayout(processing_frame_layout)

        # --- Prevent Widget expansion ---
        processing_frame_layout.setColumnStretch(0, 0)
        processing_frame_layout.setColumnStretch(1, 0)
        processing_frame_layout.setColumnStretch(2, 0)
        processing_frame_layout.setColumnStretch(3, 1)

        source_label = QLabel(text="Source: ")
        comp_label = QLabel(text="Comp: ")
        rename_label = QLabel(text="Rename Pics: ")
        self.source_lineEdit = QLineEdit()
        self.comp_lineEdit = QLineEdit()
        self.rename_lineEdit = QLineEdit()
        self.browse_button = QPushButton("Browse")
        self.process_button = QPushButton("Process")

        # --- Labels ---
        processing_frame_layout.addWidget(source_label, 0, 0)
        processing_frame_layout.addWidget(comp_label, 1, 0)
        processing_frame_layout.addWidget(rename_label, 3, 0)

        # --- line edits ---
        lineEdit_width = self.MIN_IMAGE_WIDTH - 40
        self.source_lineEdit.setFixedWidth(lineEdit_width)
        self.comp_lineEdit.setFixedWidth(lineEdit_width)
        self.rename_lineEdit.setFixedWidth(lineEdit_width)

        self.source_lineEdit.setDisabled(True)
        self.comp_lineEdit.setDisabled(True)

        self.source_lineEdit.textChanged.connect(self.enable_process_button)

        processing_frame_layout.addWidget(self.source_lineEdit, 0, 1)
        processing_frame_layout.addWidget(self.comp_lineEdit, 1, 1)
        processing_frame_layout.addWidget(self.rename_lineEdit, 3, 1)

        # --- Buttons ---
        self.process_button.setDisabled(True)

        self.browse_button.clicked.connect(self.select_file_dialog)
        self.process_button.clicked.connect(self.process_images)

        processing_frame_layout.addWidget(self.browse_button, 0, 2)
        processing_frame_layout.addWidget(self.process_button, 3, 2)

        processing_frame_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.add_widget_to_grid(processing_frame, 0, 0)

    def create_settings_frame(self) -> None:
        settings_frame = QWidget()
        settings_frame_layout = QGridLayout()

        settings_frame_layout.setColumnStretch(0, 0)
        settings_frame_layout.setColumnStretch(1, 0)
        settings_frame_layout.setColumnStretch(2, 0)
        settings_frame_layout.setColumnStretch(3, 1)

        settings_frame.setLayout(settings_frame_layout)

        # --- Quality Selection ---
        self.high_quality_radio_button = QRadioButton("High Quality")
        self.medium_quality_radio_button = QRadioButton("Medium Quality")
        self.low_quality_radio_button = QRadioButton("Low Quality")
        self.standards_quality_CheckBox = QCheckBox("Set to standards file size")

        self.medium_quality_radio_button.setChecked(True)
        self.standards_quality_CheckBox.setChecked(True)

        self.quality_button_group = QButtonGroup(settings_frame)
        self.quality_button_group.addButton(self.high_quality_radio_button, 0)
        self.quality_button_group.addButton(self.medium_quality_radio_button, 1)
        self.quality_button_group.addButton(self.low_quality_radio_button, 2)

        settings_frame_layout.addWidget(self.high_quality_radio_button, 0, 0)
        settings_frame_layout.addWidget(self.medium_quality_radio_button, 0, 1)
        settings_frame_layout.addWidget(self.low_quality_radio_button, 0, 2)
        settings_frame_layout.addWidget(self.standards_quality_CheckBox, 0, 3)

        # --- Resize Selection ---
        self.disable_resize_radio_button = QRadioButton("Disable Image Resize?")
        self.custom_resize_radio_button = QRadioButton("Input Custom Resize?")
        self.resize_line_edit = QLineEdit()

        self.disable_resize_radio_button.setChecked(True)
        self.resize_line_edit.setText("2048")
        self.resize_line_edit.setFixedWidth(240)

        self.disable_resize_radio_button.toggled.connect(self.disable_resize_line_edit)

        self.resize_button_group = QButtonGroup(settings_frame)
        self.resize_button_group.addButton(self.disable_resize_radio_button, 4)
        self.resize_button_group.addButton(self.custom_resize_radio_button, 5)

        settings_frame_layout.addWidget(self.disable_resize_radio_button, 1, 0)
        settings_frame_layout.addWidget(self.custom_resize_radio_button, 1, 1)
        settings_frame_layout.addWidget(self.resize_line_edit, 1, 2, 1, 2)

        # --- Image File output Type Selection ---
        jpeg_radio_button = QRadioButton("Compress to JPEG")
        AVIF_radio_button = QRadioButton("Compress to AVIF")
        JPEGXL_radio_button = QRadioButton("Compress to JPEG XL")
        png_radio_button = QRadioButton("Compress to PNG")

        jpeg_radio_button.setChecked(True)
        png_radio_button.toggled.connect(self.disable_quality_buttons)

        self.file_type_button_group = QButtonGroup(settings_frame)
        self.file_type_button_group.addButton(jpeg_radio_button, 6)
        self.file_type_button_group.addButton(AVIF_radio_button, 7)
        self.file_type_button_group.addButton(JPEGXL_radio_button, 8)
        self.file_type_button_group.addButton(png_radio_button, 9)

        settings_frame_layout.addWidget(jpeg_radio_button, 2, 0)
        settings_frame_layout.addWidget(AVIF_radio_button, 2, 1)
        settings_frame_layout.addWidget(JPEGXL_radio_button, 2, 2)
        settings_frame_layout.addWidget(png_radio_button, 2, 3)

        # --- Image Editing Selection ---
        self.colour_enhancement_checkbox = QCheckBox("Enable Colour Enhancement?")
        self.sharpness_enhancement_checkbox = QCheckBox("Enable Sharpness Enhancement?")
        self.image_trim_checkbox = QCheckBox("Enable Image Trim?")

        self.image_trim_checkbox.setChecked(True)

        settings_frame_layout.addWidget(self.colour_enhancement_checkbox, 3, 0)
        settings_frame_layout.addWidget(self.sharpness_enhancement_checkbox, 3, 1)
        settings_frame_layout.addWidget(self.image_trim_checkbox, 3, 2)

        settings_frame_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.add_widget_to_grid(settings_frame, 1, 0)

    def create_results_frame(self):
        RESULTS_TEXTEDIT_WIDTH = 700

        results_frame = QWidget()
        results_frame_layout = QGridLayout()

        results_frame.setLayout(results_frame_layout)

        results_frame_layout.setColumnStretch(0, 0)
        results_frame_layout.setColumnStretch(1, 1)
        results_frame_layout.setRowStretch(1, 0)

        results_label = QLabel("Results:")
        self.results_TextEdit = QTextEdit()

        self.results_TextEdit.setMinimumWidth(RESULTS_TEXTEDIT_WIDTH)
        self.results_TextEdit.setMaximumHeight(100)

        results_frame_layout.addWidget(results_label, 0, 0)
        results_frame_layout.addWidget(self.results_TextEdit, 1, 0)

        results_frame_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.add_widget_to_grid(results_frame, 2, 0)

    def create_image_frame(self):
        self.image_label = QLabel()

        main_image = QImage(self.resource_path("AutoPicsLogo.png"))
        self._original_pixmap = QPixmap(main_image)

        self.image_label.setPixmap(self._original_pixmap)

        # allow the label itself to grow
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.image_label.setMinimumSize(1, 1)  # keep the tiny-window case happy
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # put it in the grid **without** the centre-alignment flag
        self.app_layout.addWidget(self.image_label, 3, 0)  # no alignment arg here

    def resizeEvent(self, event):
        if hasattr(self, "_original_pixmap") and not self._original_pixmap.isNull():
            label_size = self.image_label.size()
            scaled_pix = self._original_pixmap.scaled(
                label_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled_pix)
        super().resizeEvent(event)

    def get_dic_standards(self) -> dict[str, str]:
        fallback_standards: dict[str, Any] = {
            "standardImageResize": "2048",
            "standardColor": "1.2",
            "standardSharpness": "2.0",
            "yourStandardsMozjpegQuality": "94",
            "highQualityMozjpegQuality": "90",
            "mediumQualityMozjpegQuality": "75",
            "lowQualityMozjpegQuality": "50",
            "standardMaxYourStandardsFileSizeInBytes": 614400,
        }
        try:
            with open(self.resource_path("defaults.txt"), "r") as file:
                print("Standards file found")
                d = {}
                for line in file:
                    (key, val) = line.split()
                    d[key] = val
                return d
        except FileNotFoundError:
            d = fallback_standards
            return d
        except IOError:
            d = fallback_standards
            return d

    def resource_path(self, relative_path: str | Path) -> Path:
        """Get absolute path to resource, works for dev and for PyInstaller"""
        if hasattr(sys, "_MEIPASS"):
            # Running in a PyInstaller bundle
            base_path = Path(sys._MEIPASS)  # type: ignore
        else:
            # Running in normal dev mode
            base_path = Path(__file__).resolve().parent

        return base_path / relative_path

    def disable_quality_buttons(self, checked: bool) -> None:
        """We use this to disable the quality settings as they are not implemented for saving to png."""
        if checked:
            self.high_quality_radio_button.setDisabled(True)
            self.medium_quality_radio_button.setDisabled(True)
            self.low_quality_radio_button.setDisabled(True)
            self.standards_quality_CheckBox.setDisabled(True)
        else:
            self.high_quality_radio_button.setDisabled(False)
            self.medium_quality_radio_button.setDisabled(False)
            self.low_quality_radio_button.setDisabled(False)
            self.standards_quality_CheckBox.setDisabled(False)

    @Slot(bool)
    def disable_resize_line_edit(self, checked: bool) -> None:
        """Toggle to disable the resize line edit when the disable radiobutton is toggled"""
        if checked:
            self.resize_line_edit.setDisabled(True)
        else:
            self.resize_line_edit.setDisabled(False)

    @Slot()
    def enable_process_button(self) -> None:
        """Fired when the source line edit is filled\n
        It then check if both have text.\n
        if the do enable the proces button."""
        source_line_edit_text = self.source_lineEdit.text().strip()

        if source_line_edit_text != "":
            self.process_button.setDisabled(False)

    @Slot()
    def select_file_dialog(self) -> None:
        self.files, _ = QFileDialog.getOpenFileNames(
            parent=self,
            caption="Select Images",
            filter=f"{self.SUFFIXES};;All Files (*)",
        )
        if self.files:
            print(self.files)
            source_folder: Path = Path(self.files[0]).parent
            self.source_lineEdit.setText(str(source_folder))

            comp_folder_name = Path(self.files[0]).stem
            self.comp_folder_path = Path(self.source_lineEdit.text(), comp_folder_name)
            self.comp_lineEdit.setText(str(self.comp_folder_path))

    @Slot()
    def process_images(self) -> None:
        self.process_button.setDisabled(True)
        self.results_TextEdit.setText("")
        encoders = {
            6: "jpeg",
            7: "avif",
            8: "jxl",
            9: "PNG",
        }
        source_folder = Path(self.source_lineEdit.text())
        comp_folder = self.comp_folder_path
        rename = self.rename_lineEdit.text()
        try:
            custom_resize_value = int(self.resize_line_edit.text())
        except ValueError as e:
            self.error_message_box(
                f"ERROR! {e}",
                "Resize text field does not contain a number. Please try again.",
                QMessageBox.Icon.Critical,
            )
            return

        # ---
        if custom_resize_value > 50000 or custom_resize_value <= 10:
            self.error_message_box(
                "Error! Image Resize value out of bounds.",
                "Please input photo dimensions larger than 10 pixels and smaller than 50000 (Have more than 20GB ram for photos this big)",
                QMessageBox.Icon.Critical,
            )
            return

        # --- Getting selected encoder ---
        file_btn_id: int = self.file_type_button_group.checkedId()
        selected_encoder = encoders.get(file_btn_id)

        if selected_encoder is None:
            self.error_message_box(
                "ERROR! No encoder set.",
                "Please select jpeg, avif, Jpeg XL or png and try again.",
                QMessageBox.Icon.Critical,
            )
            return

        # --- Checking if the rename field is correct ---
        restricted_chars = ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]
        contains_restricted = any(char in rename for char in restricted_chars)
        if contains_restricted:
            self.error_message_box(
                "ERROR! The rename field contains restricted characters",
                "Test can not contain any of these characters\n \\, ', /, :, *, ?, \", <, >, |",
                QMessageBox.Icon.Critical,
            )
            return

        # --- Creating comp folder & Checking if source and comp folders exist.
        Path.mkdir(self.comp_folder_path, exist_ok=True)

        if not Path.is_dir(source_folder) or not Path.is_dir(comp_folder):
            self.error_message_box(
                "ERROR! Source or comp folder does not exist",
                "Please try again.",
                QMessageBox.Icon.Critical,
            )
            return

        self.timer = QTimer()
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.show_next_image)

        self.image_index = 0
        self.timer.start()

        # --- Getting Variables ---
        isChecked_disabled_risize_radio_Btn: bool = (
            self.disable_resize_radio_button.isChecked()
        )

        quality_btn_id = self.quality_button_group.checkedId()
        quality_options = {
            0: "High Quality",
            1: "Medium Quality",
            2: "Low Quality",
        }
        image_quality_selection: str | None = quality_options.get(quality_btn_id)

        resize_btn_id: int = self.resize_button_group.checkedId()
        resize_options = {
            4: False,  # disable_resize
            5: True,  # custom_resize
        }
        resize_selection: bool | None = resize_options.get(resize_btn_id)

        contrast_chbx_var: bool = self.colour_enhancement_checkbox.isChecked()
        sharpen_chbx_var: bool = self.sharpness_enhancement_checkbox.isChecked()

        trim_chbx_value: bool = self.image_trim_checkbox.isChecked()

        ensure_standards_chbx_var: bool = self.standards_quality_CheckBox.isChecked()

        dic_standards = self.get_dic_standards()

        # Start long task in background
        worker = LongTaskWorker(
            source_folder,
            comp_folder,
            selected_encoder,
            rename,
            isChecked_disabled_risize_radio_Btn,
            image_quality_selection,
            custom_resize_value,
            resize_selection,
            contrast_chbx_var,
            sharpen_chbx_var,
            dic_standards,
            trim_chbx_value,
            self.files,
            ensure_standards_chbx_var,
        )
        worker.signals.finished.connect(self.on_long_task_done)
        self.threadpool.start(worker)

    # helper used by both resizeEvent and show_next_image
    def _refresh_scaled_pixmap(self) -> None:
        """Scale the current _original_pixmap to the label size and show it."""
        if (
            hasattr(self, "_original_pixmap")
            and not self._original_pixmap.isNull()
            and self.image_label.width() > 0
            and self.image_label.height() > 0
        ):
            scaled = self._original_pixmap.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)

    @Slot()
    def show_next_image(self) -> None:
        # build / refresh list once per call so newly-created images appear
        image_paths = sorted(self.comp_folder_path.glob("*.jpg"))
        if not image_paths:
            return

        # advance the index (wrap around)
        self.image_index = (getattr(self, "image_index", 0) + 1) % len(image_paths)
        current_path = image_paths[self.image_index]

        # load the image
        img = QImage(str(current_path))
        if img.isNull():
            return  # skip unreadable files

        # keep the ORIGINAL pixmap; it will be scaled every time the window resizes
        self._original_pixmap = QPixmap.fromImage(img)

        # show it scaled to the current label size
        self._refresh_scaled_pixmap()

    @Slot()
    def on_long_task_done(self):
        self.timer.stop()
        self.set_res_txb_to_comp_results()
        self.set_image_to_end_result()

        comp_folder = self.comp_folder_path
        temp_comp_path = Path(comp_folder) / "temp-comp"
        if temp_comp_path.is_dir():
            rmtree(temp_comp_path, ignore_errors=True)
        self.process_button.setDisabled(False)

    def set_image_to_end_result(self):
        """Sets the main image to the first completed image processed. \nWill revert to logo if there is an error."""
        image_paths = []
        for ext in self.extensions:
            image_paths.extend(sorted(self.comp_folder_path.glob(ext)))

        if not image_paths:
            main_image = QImage(self.resource_path("AutoPicsLogo.png"))
            self._original_pixmap = QPixmap(main_image)
            self._refresh_scaled_pixmap()
        main_image = QImage(str(image_paths[0]))
        self._original_pixmap = QPixmap(main_image)
        self._refresh_scaled_pixmap()

    def set_res_txb_to_comp_results(self) -> None:
        """Sets the result text box to the results out put after compression is completed."""
        self.results_TextEdit.setText("")
        BRIDGE = Path(tempfile.gettempdir()) / "autopics_results_bridge.txt"
        with open(BRIDGE, "r") as file:
            self.results_TextEdit.setText(file.read())
        os.remove(BRIDGE)

    def error_message_box(
        self, message_text: str, informative_text: str, icon: QMessageBox.Icon
    ) -> None:
        no_encoder_msgBox = QMessageBox()
        no_encoder_msgBox.setStyleSheet(
            """
            * {
                color: #ecf0f1;
            }
            QMessageBox {
                background-color: #292929;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: #ecf0f1;
            }
            """
        )
        no_encoder_msgBox.setText(message_text)
        no_encoder_msgBox.setInformativeText(informative_text)
        no_encoder_msgBox.setIcon(icon)
        no_encoder_msgBox.exec()

    def add_widget_to_grid(self, widget, row, col) -> None:
        self.app_layout.addWidget(
            widget, row, col, alignment=Qt.AlignmentFlag.AlignCenter
        )

    def create_app_grid_layout(self) -> None:
        """Creates the layout for the entire app.\n
        Each section will have its own grid.\n
        This function in will place all of those sections into a grid on the app's main widget."""
        self.main_widget.setLayout(self.app_layout)

        # Give row 3 (where the image_label is) a stretch of 1
        self.app_layout.setRowStretch(3, 1)

        # Also give column 0 a stretch of 1 so the image can grow horizontally
        self.app_layout.setColumnStretch(0, 1)

    def colour_main_window(self) -> None:
        self.pallet = QPalette()
        self.pallet.setColor(QPalette.ColorRole.Window, QColor("#292929"))

        self.setStyleSheet("""
                           QPushButton, QLineEdit, QTextEdit {
                               background-color: #3c3c3c;
                               color: #ecf0f1;
                           }
                           
                           QLineEdit, QTextEdit{
                               border: 1px solid #1c1c1c;
                               border-radius: 4px;
                            }

                           QPushButton::disabled {
                               background-color: #505050;
                               color: #747474;
                           }
                           
                           QRadioButton::disabled {
                               color: #C0C0C0;
                           }

                           QCheckBox::disabled {
                                color: #C0C0C0;
                           }
                           
                           QLineEdit::disabled {
                               background-color: #505050;
                               color: #ecf0f1;
                           }
                           
                           QLabel, QRadioButton, QCheckBox {
                               color: #ecf0f1;
                           }
                           """)

    def set_window_size(self, width: int, height: int) -> None:
        self.resize(width, height)
        self.setMaximumHeight(1350)


if __name__ == "__main__":
    freeze_support()
    app = QApplication([])

    window = MainWindow()
    window.show()
    app.setPalette(window.pallet)

    _ = app.exec()
