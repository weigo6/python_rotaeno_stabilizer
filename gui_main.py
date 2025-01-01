import sys
import os
import glob
import time
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QTextEdit, QFileDialog, QLabel
)
from PySide6.QtCore import QThread, Signal
from python_rotaeno_stabilizer import RotaenoStabilizer

class VideoProcessingThread(QThread):
    update_info = Signal(str)  # 定义信号以更新信息框
    processing_done = Signal()  # 定义信号以表示处理完成

    def __init__(self, input_folder, output_folder):
        super().__init__()
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.videos = []

    def find_all_videos(self):
        videos = []
        video_extensions = [ext.lower() for ext in RotaenoStabilizer.format_to_fourcc.keys()]

        for file_path in glob.glob(os.path.join(self.input_folder, '*.*')):
            if os.path.isfile(file_path):
                _, ext = os.path.splitext(file_path)
                if ext.lower() in video_extensions:
                    videos.append(file_path)  # 直接使用完整路径
        return videos

    def run(self):
        self.videos = self.find_all_videos()
        for video in self.videos:
            start = time.time()
            self.update_info.emit(f"处理视频: {video}")
            try:
                stab_task = RotaenoStabilizer(video, self.output_folder)
                stab_task.run()  # 处理视频
            except Exception as e:
                self.update_info.emit(f"处理视频时发生错误: {str(e)}")
                break

            end = time.time()
            self.update_info.emit(f"用时：{end - start:.2f}s")
            self.update_info.emit(f"{video} 处理完成，输出到: {self.output_folder}")

        self.update_info.emit("所有视频处理完成。")
        self.processing_done.emit()  # 发射处理完成信号


class VideoProcessorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rotaeno视频处理器")
        
        # 布局
        layout = QVBoxLayout()

        # 输入文件夹选择
        self.input_label = QLabel("输入文件夹: 未选择")
        layout.addWidget(self.input_label)
        input_button = QPushButton("选择输入文件夹")
        input_button.clicked.connect(self.select_input_folder)
        layout.addWidget(input_button)

        # 输出文件夹选择
        self.output_label = QLabel("输出文件夹: 未选择")
        layout.addWidget(self.output_label)
        output_button = QPushButton("选择输出文件夹")
        output_button.clicked.connect(self.select_output_folder)
        layout.addWidget(output_button)

        # 运行信息文本框
        self.info_textbox = QTextEdit()
        self.info_textbox.setReadOnly(True)
        layout.addWidget(self.info_textbox)

        # 运行按钮
        run_button = QPushButton("开始处理视频")
        run_button.clicked.connect(self.process_videos)
        layout.addWidget(run_button)

        self.setLayout(layout)

    def select_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输入文件夹")
        if folder:
            self.input_label.setText(f"输入文件夹: {folder}")
            self.input_folder = folder

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.output_label.setText(f"输出文件夹: {folder}")
            self.output_folder = folder

    def process_videos(self):
        if not hasattr(self, 'input_folder') or not hasattr(self, 'output_folder'):
            self.info_textbox.append("请确保选择了输入和输出文件夹。")
            return

        self.info_textbox.append("开始处理视频...")

        # 启动视频处理线程
        self.video_thread = VideoProcessingThread(self.input_folder, self.output_folder)
        self.video_thread.update_info.connect(self.info_textbox.append)  # 连接信号
        self.video_thread.processing_done.connect(self.processing_complete)  # 连接处理完成信号
        self.video_thread.start()  # 启动线程

    def processing_complete(self):
        self.info_textbox.append("所有视频的处理已完成。")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoProcessorApp()
    window.show()
    sys.exit(app.exec())
