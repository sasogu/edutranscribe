from __future__ import annotations

from datetime import datetime
from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
  QApplication,
  QFileDialog,
  QComboBox,
  QHBoxLayout,
  QLabel,
  QListWidget,
  QListWidgetItem,
  QMainWindow,
  QMessageBox,
  QProgressBar,
  QPushButton,
  QPlainTextEdit,
  QSplitter,
  QStatusBar,
  QToolBar,
  QVBoxLayout,
  QWidget,
)

from ..models import LANGUAGE_PRESETS, QUALITY_PRESETS, QueueItem
from ..services.transcription import TranscriptionService


class WorkerSignals(QObject):
  started = Signal(int, str)
  progress = Signal(int, int, str)
  log = Signal(int, str)
  cancelled = Signal(int, str)
  finished = Signal(int, str)
  failed = Signal(int, str)


class TranscriptionTask(QRunnable):
  def __init__(
    self,
    row: int,
    item: QueueItem,
    quality: str,
    language: str | None,
    service: TranscriptionService,
    cancel_event: Event,
  ) -> None:
    super().__init__()
    self.row = row
    self.item = item
    self.quality = quality
    self.language = language
    self.service = service
    self.cancel_event = cancel_event
    self.signals = WorkerSignals()

  def run(self) -> None:
    try:
      self.signals.started.emit(self.row, self.item.path.name)
      self.signals.log.emit(self.row, f"Iniciando transcripcion en calidad '{self.quality}'.")
      text = self.service.transcribe(
        self.item,
        self.quality,
        language=self.language,
        progress_callback=lambda value, message: self.signals.progress.emit(self.row, value, message),
        status_callback=lambda message: self.signals.log.emit(self.row, message),
        is_cancelled=self.cancel_event.is_set,
      )
    except Exception as exc:
      if self.cancel_event.is_set():
        self.signals.cancelled.emit(self.row, str(exc))
        return
      self.signals.failed.emit(self.row, str(exc))
      return

    self.signals.finished.emit(self.row, text)


class DropListWidget(QListWidget):
  files_dropped = Signal(list)

  def __init__(self) -> None:
    super().__init__()
    self.setAcceptDrops(True)
    self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

  def dragEnterEvent(self, event) -> None:  # type: ignore[override]
    if event.mimeData().hasUrls():
      event.acceptProposedAction()
      return
    event.ignore()

  def dragMoveEvent(self, event) -> None:  # type: ignore[override]
    if event.mimeData().hasUrls():
      event.acceptProposedAction()
      return
    event.ignore()

  def dropEvent(self, event) -> None:  # type: ignore[override]
    paths = []
    for url in event.mimeData().urls():
      if url.isLocalFile():
        paths.append(url.toLocalFile())

    if paths:
      self.files_dropped.emit(paths)
      event.acceptProposedAction()
      return

    event.ignore()


class MainWindow(QMainWindow):
  def __init__(self) -> None:
    super().__init__()
    self.setWindowTitle("EduTranscribe")
    self.resize(1100, 720)

    self.thread_pool = QThreadPool(self)
    self.service = TranscriptionService()
    self.queue_items: list[QueueItem] = []
    self.current_task_row: int | None = None
    self.current_cancel_event: Event | None = None

    self.queue_list = DropListWidget()
    self.queue_list.files_dropped.connect(self.add_paths)
    self.queue_list.currentRowChanged.connect(self.show_selected_text)

    self.quality_combo = QComboBox()
    for preset in QUALITY_PRESETS:
      self.quality_combo.addItem(preset.label, preset.key)
    self.quality_combo.currentIndexChanged.connect(self.update_quality_hint)

    self.quality_hint = QLabel()
    self.quality_hint.setWordWrap(True)

    self.language_combo = QComboBox()
    for preset in LANGUAGE_PRESETS:
      self.language_combo.addItem(preset.label, preset.key)
    self.language_combo.currentIndexChanged.connect(self.update_language_hint)

    self.language_hint = QLabel()
    self.language_hint.setWordWrap(True)

    self.progress_label = QLabel("Sin tareas en curso.")
    self.progress_label.setWordWrap(True)

    self.progress_bar = QProgressBar()
    self.progress_bar.setRange(0, 100)
    self.progress_bar.setValue(0)
    self.progress_bar.setTextVisible(True)

    self.output = QPlainTextEdit()
    self.output.setReadOnly(True)
    self.output.setPlaceholderText("La transcripcion del elemento seleccionado aparecera aqui.")

    self.log_output = QPlainTextEdit()
    self.log_output.setReadOnly(True)
    self.log_output.setPlaceholderText("Los eventos del proceso apareceran aqui.")

    self.start_button = QPushButton("Transcribir seleccion")
    self.start_button.clicked.connect(self.transcribe_selected)

    self.cancel_button = QPushButton("Interrumpir")
    self.cancel_button.clicked.connect(self.cancel_transcription)
    self.cancel_button.setEnabled(False)

    self.copy_button = QPushButton("Copiar resultado")
    self.copy_button.clicked.connect(self.copy_output)
    self.copy_button.setEnabled(False)

    self.add_button = QPushButton("Anadir archivos")
    self.add_button.clicked.connect(self.pick_files)

    self.remove_button = QPushButton("Quitar seleccion")
    self.remove_button.clicked.connect(self.remove_selected)

    self.clear_button = QPushButton("Vaciar cola")
    self.clear_button.clicked.connect(self.clear_queue)

    self._build_toolbar()
    self._build_layout()

    status_bar = QStatusBar(self)
    status_bar.showMessage("Listo. Arrastra archivos o usa el boton de anadir.")
    self.setStatusBar(status_bar)

    self.update_quality_hint()
    self.update_language_hint()

  def _build_toolbar(self) -> None:
    toolbar = QToolBar("Principal", self)
    toolbar.setMovable(False)
    self.addToolBar(toolbar)

    open_action = QAction("Abrir", self)
    open_action.triggered.connect(self.pick_files)
    toolbar.addAction(open_action)

    run_action = QAction("Transcribir", self)
    run_action.triggered.connect(self.transcribe_selected)
    toolbar.addAction(run_action)

  def _build_layout(self) -> None:
    left_panel = QWidget()
    left_layout = QVBoxLayout(left_panel)
    left_layout.addWidget(QLabel("Cola"))
    left_layout.addWidget(self.queue_list, 1)

    controls = QHBoxLayout()
    controls.addWidget(self.add_button)
    controls.addWidget(self.remove_button)
    controls.addWidget(self.clear_button)
    left_layout.addLayout(controls)

    right_panel = QWidget()
    right_layout = QVBoxLayout(right_panel)
    right_layout.addWidget(QLabel("Calidad"))
    right_layout.addWidget(self.quality_combo)
    right_layout.addWidget(self.quality_hint)
    right_layout.addWidget(QLabel("Idioma"))
    right_layout.addWidget(self.language_combo)
    right_layout.addWidget(self.language_hint)
    actions = QHBoxLayout()
    actions.addWidget(self.start_button)
    actions.addWidget(self.cancel_button)
    actions.addWidget(self.copy_button)
    right_layout.addLayout(actions)
    right_layout.addWidget(QLabel("Progreso"))
    right_layout.addWidget(self.progress_label)
    right_layout.addWidget(self.progress_bar)
    right_layout.addWidget(QLabel("Salida"))
    right_layout.addWidget(self.output, 1)
    right_layout.addWidget(QLabel("Consola"))
    right_layout.addWidget(self.log_output, 1)

    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.addWidget(left_panel)
    splitter.addWidget(right_panel)
    splitter.setStretchFactor(0, 2)
    splitter.setStretchFactor(1, 3)

    root = QWidget()
    root_layout = QVBoxLayout(root)
    root_layout.addWidget(splitter)
    self.setCentralWidget(root)

  def pick_files(self) -> None:
    paths, _ = QFileDialog.getOpenFileNames(
      self,
      "Seleccionar audio o video",
      "",
      "Media files (*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.mp4 *.mov *.mkv *.webm);;All files (*)",
    )
    if paths:
      self.add_paths(paths)

  def add_paths(self, paths: list[str]) -> None:
    added = 0
    for raw_path in paths:
      path = Path(raw_path).expanduser().resolve()
      if not path.exists() or path.is_dir():
        continue
      if any(existing.path == path for existing in self.queue_items):
        continue

      queue_item = QueueItem(path=path)
      self.queue_items.append(queue_item)
      self.queue_list.addItem(self._make_row_label(queue_item))
      added += 1

    if added:
      self.statusBar().showMessage(f"Anadidos {added} archivos a la cola.")
      if self.queue_list.currentRow() == -1:
        self.queue_list.setCurrentRow(0)
      return

    self.statusBar().showMessage("No se anadio ningun archivo nuevo.")

  def remove_selected(self) -> None:
    row = self.queue_list.currentRow()
    if row < 0:
      return

    self.queue_items.pop(row)
    self.queue_list.takeItem(row)
    self.output.clear()
    self.copy_button.setEnabled(False)
    self.statusBar().showMessage("Elemento eliminado de la cola.")

  def clear_queue(self) -> None:
    self.queue_items.clear()
    self.queue_list.clear()
    self.output.clear()
    self.copy_button.setEnabled(False)
    self.statusBar().showMessage("Cola vaciada.")

  def transcribe_selected(self) -> None:
    row = self.queue_list.currentRow()
    if row < 0:
      QMessageBox.information(self, "Sin seleccion", "Selecciona un archivo de la cola primero.")
      return

    item = self.queue_items[row]
    item.status = "Procesando"
    self._refresh_row(row)
    self.start_button.setEnabled(False)
    self.cancel_button.setEnabled(True)
    self.copy_button.setEnabled(False)
    self.progress_bar.setValue(0)
    self.progress_label.setText(f"Preparando {item.path.name}...")
    self._append_log(f"[{item.path.name}] Cola -> Procesando")
    self.statusBar().showMessage(f"Procesando {item.path.name}...")

    quality = str(self.quality_combo.currentData())
    language_key = str(self.language_combo.currentData())
    language = None if language_key == "auto" else language_key
    cancel_event = Event()
    self.current_task_row = row
    self.current_cancel_event = cancel_event
    task = TranscriptionTask(
      row=row,
      item=item,
      quality=quality,
      language=language,
      service=self.service,
      cancel_event=cancel_event,
    )
    task.signals.started.connect(self._handle_started)
    task.signals.progress.connect(self._handle_progress)
    task.signals.log.connect(self._handle_log)
    task.signals.cancelled.connect(self._handle_cancelled)
    task.signals.finished.connect(self._handle_finished)
    task.signals.failed.connect(self._handle_failed)
    self.thread_pool.start(task)

  def cancel_transcription(self) -> None:
    if self.current_cancel_event is None or self.current_task_row is None:
      return

    row = self.current_task_row
    item = self.queue_items[row]
    self.current_cancel_event.set()
    self.cancel_button.setEnabled(False)
    self.progress_label.setText(f"Interrumpiendo {item.path.name}...")
    self._append_log(f"[{item.path.name}] Solicitud de cancelacion enviada")
    self.statusBar().showMessage(f"Interrumpiendo {item.path.name}...")

  def copy_output(self) -> None:
    text = self.output.toPlainText().strip()
    if not text:
      self.statusBar().showMessage("No hay transcripcion para copiar.")
      return

    clipboard = QApplication.clipboard()
    clipboard.setText(text)
    self.statusBar().showMessage("Transcripcion copiada al portapapeles.")
    self._append_log("[UI] Resultado copiado al portapapeles")

  def _handle_started(self, row: int, file_name: str) -> None:
    if row >= len(self.queue_items):
      return
    self.progress_label.setText(f"Transcribiendo {file_name}...")
    self._append_log(f"[{file_name}] Trabajo enviado al backend")

  def _handle_progress(self, row: int, value: int, message: str) -> None:
    if row >= len(self.queue_items):
      return
    item = self.queue_items[row]
    self.progress_bar.setValue(value)
    self.progress_label.setText(f"{item.path.name}: {value}%")
    self.statusBar().showMessage(f"{item.path.name}: {value}%")
    self._append_log(f"[{item.path.name}] {value}% · {message}")

  def _handle_log(self, row: int, message: str) -> None:
    if row >= len(self.queue_items):
      return
    item = self.queue_items[row]
    self._append_log(f"[{item.path.name}] {message}")

  def _handle_finished(self, row: int, text: str) -> None:
    item = self.queue_items[row]
    item.status = "Completado"
    item.text = text
    self._refresh_row(row)
    if self.queue_list.currentRow() == row:
      self.output.setPlainText(text)
    self.start_button.setEnabled(True)
    self.cancel_button.setEnabled(False)
    self.copy_button.setEnabled(True)
    self.progress_bar.setValue(100)
    self.progress_label.setText(f"Completado: {item.path.name}")
    self._append_log(f"[{item.path.name}] Transcripcion completada")
    self.statusBar().showMessage(f"Transcripcion completada: {item.path.name}")
    self._clear_running_task(row)

  def _handle_cancelled(self, row: int, message: str) -> None:
    item = self.queue_items[row]
    item.status = "Cancelado"
    self._refresh_row(row)
    self.start_button.setEnabled(True)
    self.cancel_button.setEnabled(False)
    self.progress_bar.setValue(0)
    self.progress_label.setText(f"Cancelado: {item.path.name}")
    self._append_log(f"[{item.path.name}] Cancelado · {message}")
    self.statusBar().showMessage(f"Transcripcion cancelada: {item.path.name}")
    self._clear_running_task(row)

  def _handle_failed(self, row: int, message: str) -> None:
    item = self.queue_items[row]
    item.status = "Error"
    self._refresh_row(row)
    self.start_button.setEnabled(True)
    self.cancel_button.setEnabled(False)
    self.progress_bar.setValue(0)
    self.progress_label.setText(f"Error: {item.path.name}")
    self._append_log(f"[{item.path.name}] ERROR · {message}")
    self.statusBar().showMessage(f"Error en {item.path.name}")
    self._clear_running_task(row)
    QMessageBox.critical(self, "Error de transcripcion", message)

  def show_selected_text(self, row: int) -> None:
    if row < 0 or row >= len(self.queue_items):
      self.output.clear()
      self.copy_button.setEnabled(False)
      return

    item = self.queue_items[row]
    self.output.setPlainText(item.text)
    self.copy_button.setEnabled(bool(item.text.strip()))

  def update_quality_hint(self) -> None:
    index = self.quality_combo.currentIndex()
    if index < 0:
      self.quality_hint.clear()
      return

    preset = QUALITY_PRESETS[index]
    self.quality_hint.setText(preset.description)

  def update_language_hint(self) -> None:
    index = self.language_combo.currentIndex()
    if index < 0:
      self.language_hint.clear()
      return

    preset = LANGUAGE_PRESETS[index]
    self.language_hint.setText(preset.description)

  def _append_log(self, message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    self.log_output.appendPlainText(f"{timestamp}  {message}")

  def _clear_running_task(self, row: int) -> None:
    if self.current_task_row == row:
      self.current_task_row = None
      self.current_cancel_event = None

  def _refresh_row(self, row: int) -> None:
    widget_item = self.queue_list.item(row)
    if widget_item is None:
      return
    widget_item.setText(self._make_row_label(self.queue_items[row]))

  @staticmethod
  def _make_row_label(item: QueueItem) -> str:
    return f"{item.path.name}  [{item.status}]"
