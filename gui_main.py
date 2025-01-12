import sys
import os
import glob
import time
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QHBoxLayout, QTextEdit, QFileDialog, QLabel, QMessageBox, QGroupBox, QCheckBox, QLineEdit, QSpinBox
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QThread, Signal
from python_rotaeno_stabilizer import RotaenoStabilizer

class PrintRedirector:
    def __init__(self, info_textbox):
        self.info_textbox = info_textbox

    def write(self, message):
        self.info_textbox.append(message)

    def flush(self):
        pass  # 不需要实现 flush 方法

class VideoProcessingThread(QThread):
    update_info = Signal(str)  # 定义信号以更新信息框
    processing_done = Signal()  # 定义信号以表示处理完成

    def __init__(self, input_folder, output_folder, ffmpeg_path, square, type, circle, hi_quality, O_value, S_value):
        super().__init__()
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.ffmpeg_path = ffmpeg_path
        self.square = square
        self.type = type
        self.circle = circle
        self.hi_quality = hi_quality
        self.O_value = O_value
        self.S_value = S_value
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
                if video[0:2] == "v1":
                    stab_task = RotaenoStabilizer(video, self.output_folder, ffmpeg_path=self.ffmpeg_path, square=self.square, type="v1", circle=self.circle, hi_quality=self.hi_quality,O_value=self.O_value, S_value=self.S_value)
                else:
                    stab_task = RotaenoStabilizer(video, self.output_folder, ffmpeg_path=self.ffmpeg_path, square=self.square, type=self.type, circle=self.circle, hi_quality=self.hi_quality,O_value=self.O_value, S_value=self.S_value)
                stab_task.run()  # 处理视频
            except Exception as e:
                self.update_info.emit(f"处理视频时发生错误: {str(e)}")
                break

            end = time.time()
            self.update_info.emit(f"用时：{end - start:.2f}s")
            self.update_info.emit(f"{video} 处理完成，输出到: {self.output_folder}")

        self.update_info.emit("Happy End!")
        self.processing_done.emit()  # 发射处理完成信号

class VideoProcessorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rotaeno录屏稳定工具")

        # 判断当前运行环境
        if getattr(sys, 'frozen', False):
            # 应用在打包后的环境中运行
            base_path = sys._MEIPASS  # Nuitka 与 PyInstaller 相似，使用这个路径
        else:
            # 应用在开发环境中运行
            base_path = os.path.dirname(os.path.abspath(__file__))
        # 拼接完整路径
        icon_path = os.path.join(base_path, "tabler_universe.png")
        self.setWindowIcon(QIcon(icon_path))

        # 设置窗口大小
        #self.setFixedSize(600, 700)  # 设置固定窗口大小为600x700像素

        # 初始化 ffmpeg_path
        self.ffmpeg_path = None
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)  # 设置边距
        main_layout.setSpacing(10)  # 设置控件间距
        
        # 工具标题
        self.input_label = QLabel("Rotaeno录屏稳定工具")
        self.input_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(self.input_label)

        # 输入文件夹选择
        input_layout = QHBoxLayout()  # 使用 QHBoxLayout 使按钮和标签在同一行
        self.input_folder_line_edit = QLineEdit("未选择")  # 使用 QLineEdit 替代 QLabel
        self.input_folder_line_edit.setReadOnly(True)  # 设置为只读
        self.input_folder_line_edit.setStyleSheet("font-size: 13px;")
        input_layout.addWidget(self.input_folder_line_edit)

        input_button = QPushButton("选择输入文件夹")
        input_button.setFixedWidth(100)  # 设置按钮宽度
        input_button.clicked.connect(self.select_input_folder)
        input_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 12px; padding: 5px; border-radius: 5px;")
        input_layout.addWidget(input_button)

        main_layout.addLayout(input_layout)

        # 输出文件夹选择
        output_layout = QHBoxLayout()  # 使用 QHBoxLayout 使按钮和文本框在同一行
        self.output_folder_line_edit = QLineEdit("未选择")  # 使用 QLineEdit 替代 QLabel
        self.output_folder_line_edit.setReadOnly(True)  # 设置为只读
        self.output_folder_line_edit.setStyleSheet("font-size: 13px;")
        output_layout.addWidget(self.output_folder_line_edit)

        output_button = QPushButton("选择输出文件夹")
        output_button.setFixedWidth(100)  # 设置按钮宽度
        output_button.clicked.connect(self.select_output_folder)
        output_button.setStyleSheet("background-color: #2196F3; color: white; font-size: 12px; padding: 5px; border-radius: 5px;")
        output_layout.addWidget(output_button)

        main_layout.addLayout(output_layout)

        # FFmpeg 路径提示及按钮布局
        ffmpeg_layout = QHBoxLayout()       
        self.ffmpeg_label = QLabel("正在检查 FFmpeg 路径。")
        #self.ffmpeg_label.setFixedWidth(300)  # 根据需要调整宽度
        self.ffmpeg_label.setWordWrap(True)   #启用自动换行
        ffmpeg_layout.addWidget(self.ffmpeg_label)

        select_ffmpeg_btn = QPushButton("手动选择 ffmpeg.exe")
        select_ffmpeg_btn.setFixedWidth(130)  # 设置按钮宽度
        select_ffmpeg_btn.clicked.connect(self.select_ffmpeg_path)
        select_ffmpeg_btn.setStyleSheet("background-color: #9C27B0; color: white; font-size: 12px; padding: 5px; border-radius: 5px;")
        ffmpeg_layout.addWidget(select_ffmpeg_btn)

        main_layout.addLayout(ffmpeg_layout)

        # 复选框组布局
        checkbox_layout = QVBoxLayout()
        checkbox_layout.setSpacing(10)  # 设置复选框之间的间距

        # 创建方形渲染和圆形蒙版的横向布局
        shape_layout = QHBoxLayout()
        self.square_checkbox = QCheckBox("方形渲染square")
        self.square_checkbox.setChecked(True)
        shape_layout.addWidget(self.square_checkbox)

        self.circle_checkbox = QCheckBox("圆形蒙版circle")
        self.circle_checkbox.setChecked(False)
        shape_layout.addWidget(self.circle_checkbox)

        # 将横向布局添加到复选框布局
        checkbox_layout.addLayout(shape_layout)

        # 创建高码率输出和使用类型‘v2’的横向布局
        type_layout = QHBoxLayout()
        self.hi_q_checkbox = QCheckBox("高码率输出hi_q")
        self.hi_q_checkbox.setChecked(False)
        type_layout.addWidget(self.hi_q_checkbox)

        self.type_checkbox = QCheckBox("使用类型 v2（type='v2'）")
        self.type_checkbox.setChecked(True)
        type_layout.addWidget(self.type_checkbox)

        # 将横向布局添加到复选框布局
        checkbox_layout.addLayout(type_layout)

        # 创建偏移值输入框
        spin_layout = QHBoxLayout()
        self.O_spin_box = QSpinBox()
        self.O_spin_box.setPrefix("采集颜色块偏移值: ")  # 设置前缀
        self.O_spin_box.setRange(0, 5)  # 设置范围为0到5
        self.O_spin_box.setValue(3)       # 设置默认值
        self.O_spin_box.setSingleStep(1)   # 设置每次增加或减少的步进值
        spin_layout.addWidget(self.O_spin_box)

        # 创建区域大小输入框
        self.S_spin_box = QSpinBox()
        self.S_spin_box.setPrefix("采集颜色块区域大小: ")  # 设置前缀
        self.S_spin_box.setRange(1, 5)  # 设置范围为1到5
        self.S_spin_box.setValue(3)       # 设置默认值
        self.S_spin_box.setSingleStep(1)   # 设置每次增加或减少的步进值
        spin_layout.addWidget(self.S_spin_box)

        # 将横向布局添加到复选框布局
        checkbox_layout.addLayout(spin_layout)

        #添加描述标签
        self.spin_label = QLabel("若输出视频无偏转问题，偏移值和区域大小设置请采用默认值。")
        checkbox_layout.addWidget(self.spin_label)

        # 添加描述标签
        self.type_label = QLabel("v2模式下，在视频文件名称前添加v1字样，将对该文件以v1模式进行处理。")
        checkbox_layout.addWidget(self.type_label)

        # 复选框组
        checkbox_group = QGroupBox("设置选项")
        checkbox_group.setLayout(checkbox_layout)
        main_layout.addWidget(checkbox_group)
       
        # 按钮行布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # 设置按钮之间的间距

        # 开始处理视频按钮
        run_button = QPushButton("开始处理视频")
        run_button.clicked.connect(self.process_videos)
        run_button.setStyleSheet("background-color: #FF5722; color: white; font-size: 14px; padding: 6px; border-radius: 5px;")
        #run_button.setFixedWidth(200)  # 设置按钮宽度
        button_layout.addWidget(run_button)

        # 打开输出文件夹按钮
        open_output_button = QPushButton("打开输出文件夹")
        open_output_button.setFixedWidth(150)  # 设置按钮宽度
        open_output_button.clicked.connect(self.open_output_folder)
        open_output_button.setStyleSheet("background-color: #FFC107; color: black; font-size: 12px; padding: 5px; border-radius: 5px;")        
        button_layout.addWidget(open_output_button)

        # 程序说明按钮
        help_button = QPushButton("程序说明")
        help_button.setFixedWidth(100)  # 设置按钮宽度
        help_button.clicked.connect(self.show_help)
        help_button.setStyleSheet("background-color: #03A9F4; color: white; font-size: 12px; padding: 5px; border-radius: 5px;")        
        button_layout.addWidget(help_button)

        main_layout.addLayout(button_layout)

        # 创建输出信息区
        self.output_group_box = QGroupBox("程序运行进程提示:")
        self.info_textbox = QTextEdit()
        self.info_textbox.setReadOnly(True)

        output_layout = QVBoxLayout()
        output_layout.addWidget(self.info_textbox)
        self.output_group_box.setLayout(output_layout)

        main_layout.addWidget(self.output_group_box)

        # 将主布局设置为窗体布局
        self.setLayout(main_layout)

        # 将标准输出重定向到 QTextEdit
        sys.stdout = PrintRedirector(self.info_textbox)

        # 启动时自动检查 FFmpeg 路径
        self.find_ffmpeg()

        # 连接 square_checkbox 状态变化信号
        self.square_checkbox.toggled.connect(self.update_circle_checkbox_state)

    def update_circle_checkbox_state(self):
        # 仅在 square_checkbox 被选中时才能选择 circle_checkbox
        is_square_checked = self.square_checkbox.isChecked()
        self.circle_checkbox.setEnabled(is_square_checked)

    def find_ffmpeg(self):
        self.ffmpeg_path = self.get_ffmpeg_path()
        if self.ffmpeg_path:
            self.ffmpeg_label.setText(f"选择的 FFmpeg 路径: \n{self.ffmpeg_path}\n当前无需手动选择ffmpeg路径。")
        else:
            self.ffmpeg_label.setText("未找到 FFmpeg，请手动选择路径。")

    def get_ffmpeg_path(self):
        # 1. 先检查当前工作目录下的 ffmpeg/bin
        current_dir = os.getcwd()
        ffmpeg_bin_dir = os.path.join(current_dir, 'ffmpeg', 'bin')  # 构造 ffmpeg/bin 路径
        ffmpeg_executable = os.path.join(ffmpeg_bin_dir, 'ffmpeg')  # 这里是无扩展名的路径
        if os.path.isfile(ffmpeg_executable) and os.access(ffmpeg_executable, os.X_OK):
            return ffmpeg_executable

        # Windows 特殊处理
        ffmpeg_executable_with_ext = ffmpeg_executable + '.exe'
        if os.path.isfile(ffmpeg_executable_with_ext) and os.access(ffmpeg_executable_with_ext, os.X_OK):
            return ffmpeg_executable_with_ext
        
        # 2. 若当前目录ffmpeg/bin/ffmpeg.exe文件不存在，检查系统 PATH 是否存在ffmpeg
        for path in os.environ['PATH'].split(os.pathsep):
            ffmpeg_executable = os.path.join(path, 'ffmpeg')
            if os.path.isfile(ffmpeg_executable) and os.access(ffmpeg_executable, os.X_OK):
                return ffmpeg_executable
            
            # Windows 特殊处理
            ffmpeg_executable_with_ext = ffmpeg_executable + '.exe'
            if os.path.isfile(ffmpeg_executable_with_ext) and os.access(ffmpeg_executable_with_ext, os.X_OK):
                return ffmpeg_executable_with_ext

        return None

    def select_ffmpeg_path(self):
        # 通过文件对话框让用户选择 ffmpeg 路径
        file_name, _ = QFileDialog.getOpenFileName(self, "选择 FFmpeg 可执行文件", "", "可执行文件 (*.exe);;所有文件 (*)")   
        if file_name:
            self.ffmpeg_path = file_name  # 更新类属性
            QMessageBox.information(self, "选择结果", f"选择的 FFmpeg 路径: \n{file_name}")
            self.ffmpeg_label.setText(f"选择的 FFmpeg 路径: \n{file_name}")
        else:
            QMessageBox.warning(self, "错误", "选择的文件不是有效的可执行文件，或没有执行权限。")

    def select_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输入文件夹")
        if folder:
            self.input_folder_line_edit.setText(folder)  # 设置输入文件夹路径
            self.input_folder = folder

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.output_folder_line_edit.setText(folder)  # 设置输出文件夹路径
            self.output_folder = folder

    def open_output_folder(self):
        if hasattr(self, 'output_folder') and os.path.isdir(self.output_folder):
            try:
                os.startfile(self.output_folder)  # 使用 os.startfile 打开输出文件夹，仅在windows上有效
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法打开输出文件夹: {str(e)}")
        else:
            QMessageBox.warning(self, "错误", "请先选择输出文件夹。")

    def process_videos(self):
        if not hasattr(self, 'input_folder') or not os.path.isdir(self.input_folder):
            self.input_folder = os.path.join(os.getcwd(), 'videos')  # 设置默认输入文件夹路径
            self.info_textbox.append(f"未选择输入文件夹，使用默认路径: {self.input_folder}")
            if not os.path.exists(self.input_folder):
                self.info_textbox.append(f"检测到默认路径: {self.input_folder}不存在，请选择输入文件夹。")
                return

        if not hasattr(self, 'output_folder') or not os.path.isdir(self.output_folder):
            self.output_folder = os.path.join(os.getcwd(), 'output')  # 设置默认输出文件夹路径
            self.info_textbox.append(f"输出文件夹不存在，使用默认路径: {self.output_folder}")
        
        # 检查 FFmpeg 路径     
        if not self.ffmpeg_path:
            self.info_textbox.append("请确保选择了 FFmpeg 可执行文件。")
            return

        square = self.square_checkbox.isChecked()
        circle = self.circle_checkbox.isChecked()
        hi_quality = self.hi_q_checkbox.isChecked()
        type_v = "v2" if self.type_checkbox.isChecked() else "v1"
        O_value = self.O_spin_box.value()  # 获取当前值
        S_value = self.S_spin_box.value()  # 获取当前值
        self.info_textbox.append("开始处理视频...")

        # 启动视频处理线程
        print(f"使用的 FFmpeg 路径: {self.ffmpeg_path}")
        self.video_thread = VideoProcessingThread(self.input_folder, self.output_folder, self.ffmpeg_path, square, type_v, circle, hi_quality, O_value, S_value)
        self.video_thread.update_info.connect(self.info_textbox.append)
        self.video_thread.processing_done.connect(self.processing_complete)
        self.video_thread.start()

    def processing_complete(self):
        self.info_textbox.append("所有视频的处理已完成。")

    def show_help(self):
        help_message = "程序说明:\n\n" \
                       "！！！本工具所支持的视频必须是在游戏设置中打开直播编码v2的情况下的录制视频。\n请注意录制的游戏视频必须铺满整个画面，否则无法捕获四角颜色用于对视频帧进行旋转操作。\n" \
                       "1. 选择输入文件夹，包含要处理的视频文件，本工具支持批量转换。\n" \
                       "2. 选择输出文件夹，处理后的视频将保存在此文件夹中。\n" \
                       "3. 当不选择输入输出文件夹时，使用默认路径，输入文件夹默认路径为程序当前目录下的videos文件夹，输出文件夹默认为程序当前目录下的output文件夹。\n" \
                       "4. 默认的输出文件夹output如果不存在，程序会自动创建该文件夹。\n" \
                       "5. 程序需要ffmpeg工具对视频进行处理。程序运行时会优先尝试当前程序目录下的ffmpeg/bin/ffmpeg.exe\n   如果当前目录下不存在ffmpeg，则会尝试从系统环境变量中找到ffmpeg。\n"\
                       "   这样设计的好处是若已安装并将ffmpeg添加到系统环境中，程序会自动获取ffmpeg路径，只需要单个exe文件就能运行。\n" \
                       "6. 如果程序没有自动获取到ffmpeg路径，您可以点击‘手动选择 ffmpeg.exe’ 按钮手动添加ffmpeg路径。\n" \
                       "7. 方形渲染将在输出画面中绘制圆形。\n" \
                       "8. 圆形蒙版将方形渲染的视频通过圆形裁剪后输出，圆形蒙版只能在启用方形渲染的前提下启用。\n" \
                       "9. 高码率输出将获得更好地视频质量，但是文件大小和导出时间都将大幅增加。\n" \
                       "10. 取消勾选启用模式v2将强制以v1模式进行视频转化。启动v2模式的前提下，在视频文件前加v1，将对该视频文件以v1模式进行处理。\n" \
                       "11. 程序通过获取四角的颜色值进行每帧的旋转角度计算。\n"\
                       "12. 采集颜色块偏移值指从画面边缘的偏移量，单位为像素，默认值为 3 像素，范围为0-5。\n"\
                       "13. 采集颜色块大小指采集的样本区域大小，单位为像素，默认值为 3 像素，范围为1-5。\n"\
                       "14. 一般情况下请采用默认的采集颜色块偏移值和采集颜色块大小，当输出帧存在旋转角度偏转问题时请尝试调整偏移量和采样区域。\n"\
                       "15. 处理完成后，可以点击'打开输出文件夹'按钮查看输出的视频。\n"\
                       "版权声明：\n"\
                       "        This product includes software developed at \n"\
                       "Original Project python_rotaeno_stabilizer(https://github.com/Lawrenceeeeeeee/python_rotaeno_stabilizer/tree/master)\n"\
                       "        Original Copyright (c) 2023 Lawrence Guo\n            Modifications Copyright 2025 luwei "

        QMessageBox.information(self, "程序说明", help_message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoProcessorApp()
    window.show()
    sys.exit(app.exec())
