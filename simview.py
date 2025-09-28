# -*- coding: utf-8 -*-
"""
Created on Sun Nov  7 20:08:04 2021
@author: Zdeněk Tošner
Changelog:
v1.0 by Zdeněk Tošner
v1.1 added shortcut to almost all functions for faster workflow.
"""
# Enter simpson executable related information here
SIMPSON_EXECUTABLE="C:\\data\\vypocty\\local\\simpson_win_10\\simpson-w10.exe"
SIMPSON_TCL_LIBRARY="C:\\data\\vypocty\\local\\simpson_win_10\\tcl8.6"
SIMPSON_LD_LIBRARY_PATH=""
SIMPSON_EXAMPLES_PATH="C:\\data\\workspace_before_2021\\simpson_GUI\\newer\\examples"
LOCALE_ENCODING="cp852"  # to find out on windows, execute in cmd.exe command chcp
EDITOR_FONT_SIZE=11

#These settings worked flawlessly on a fresh Ubuntu 21.04 install

#SIMPSON_EXECUTABLE="/usr/share/simpson/simpson4.2.1"
#SIMPSON_TCL_LIBRARY="/usr/share/tcltk/tcl8.6"
#SIMPSON_LD_LIBRARY_PATH="/usr/share/simpson"

# -------- DO  NOT  EDIT  BELOW  THIS  LINE  -----------

from PyQt5.QtCore import Qt, QRegExp, QProcess, QLocale
from PyQt5.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QFontDatabase, QCursor, QKeySequence
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QPlainTextEdit, QLabel, QFrame, QSplitter, QToolBar, QCheckBox, QAction, QMessageBox, QFileDialog, QLineEdit, QMenu, QSizePolicy, QShortcut, QInputDialog, QDialog, QListWidget, QPushButton, QDoubleSpinBox)
import sys, os, glob
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np


class MainWindow(QMainWindow):
    
    # constructor
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # default values of global variables
        self.input_file_name = None
        self.input_file_changed = False
        self.input_file_is_example = False
        self.simpson_process = None  # indicator of running simpson calculation

        # setting main window geometry
        self.setGeometry(100, 100, 800, 600)

        # create simpson code editor
        self.editor = QPlainTextEdit()
        # changing line wrap mode - we do not want long lines to wrap - possible problem in TCL interpretation
        self.editor.setLineWrapMode(0)
        # setting font to the editor
        # fixedfont = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        fixedfont = QFont()
        fixedfont.setPointSize(EDITOR_FONT_SIZE)
        self.editor.setFont(fixedfont)
        # to indicate text change, call special function to indicate it in the title
        self.editor.document().modificationChanged.connect(self.editor_text_changed)
        # connect syntax highlighter
        self.highlighter = Highlighter(self.editor.document())
        # create simpson output text box
        self.simpsonoutput = QPlainTextEdit()
        self.simpsonoutput.setReadOnly(True)
                
        # arrange editor and simpson output to a splitter (left part of the main window)
        self.textsplitter = QSplitter(Qt.Vertical)
        # embed editor in its own frame and add it to the splitter
        editorframe = QFrame()
        layout = QVBoxLayout()
        layout.addWidget(self.editor)
        editorframe.setLayout(layout)
        editorframe.setStyleSheet("background-color: rgb(255, 255, 204)")
        self.textsplitter.addWidget(editorframe)
        # embed simpson output label and textbox in its own frame and add it to the splitter
        outputframe = QFrame()
        layout = QVBoxLayout()
        lbl = QLabel();
        lbl.setText("SIMPSON output")
        layout.addWidget(lbl)
        layout.addWidget(self.simpsonoutput)
        outputframe.setLayout(layout)
        outputframe.setStyleSheet("background-color: rgb(255, 204, 204)")
        self.textsplitter.addWidget(outputframe)
        # adjust initial sizes of the splitter (sum matches main window height)
        self.textsplitter.setSizes([600,200])

        # Create the maptlotlib FigureCanvas object,
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        
        # layout of the central widget will be in a splitter container (horizontally)
        self.mainsplitter = QSplitter(Qt.Horizontal)
        # adding textframes (= editor and output, contained in the first splitter) to the layout
        self.mainsplitter.addWidget(self.textsplitter)
        # adding canvas to the layout
        self.mainsplitter.addWidget(self.canvas)
        # adjusting initial sizes (sum matches main window width)
        self.mainsplitter.setSizes([300,300])
        self.storedMainSplitterSizes = self.mainsplitter.sizes()
        # add the splitter as centra widget
        self.setCentralWidget(self.mainsplitter)
        
        # create Editor toolbar
        editorbar = QToolBar("Editor tools")
        showeditorcontrol = QCheckBox("Show editor");
        showeditorcontrol.setChecked(True)
        showeditorcontrol.setToolTip("Hide / Show text editor")
        showeditorcontrol.stateChanged.connect(self.hideEditor)
        editorbar.addWidget(showeditorcontrol)
        #   find dialog
        lbl = QLabel()
        lbl.setText("  Find:")
        editorbar.addWidget(lbl)
        self.findentry = QLineEdit()
        fm = self.findentry.fontMetrics()
        self.findentry.setFixedWidth(16*fm.width('x'))
        self.findentry.textEdited.connect(self.findTextHighlight)
        editorbar.addWidget(self.findentry)
        # spacer
        toolbarspacer = QLabel();
        toolbarspacer.setText("Chart: ")
        toolbarspacer.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        toolbarspacer.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        # toolbarspacer.setStyleSheet("background-color: rgb(100, 204, 204)")
        # editorbar.addWidget(toolbarspacer)
        # matplotlib toolbar
        # mpl_toolbar = NavigationToolbar2QT(self.canvas, self)
        # editorbar.addWidget(mpl_toolbar)
        self.addToolBar(editorbar)
        chartbar = QToolBar("Chart tools")
        chartbar.addWidget(toolbarspacer)
        toolcursor = QCheckBox("Crosshair ")
        toolcursor.setChecked(False)
        toolcursor.setShortcut('Ctrl+Q')
        toolcursor.setToolTip("Toggle crosshair cursor Crtl+Q")
        toolcursor.clicked.connect(self.canvas.handle_crosshair_cursor)
        self.canvas.addToolcursor(toolcursor)
        chartbar.addWidget(toolcursor)
        toolxreverse = QCheckBox("x-reverse ")
        toolxreverse.setChecked(False)
        toolxreverse.setToolTip("Toggle x-axis direction")
        toolxreverse.clicked.connect(self.canvas.handle_xrev)
        self.canvas.addToolxrev(toolxreverse)
        chartbar.addWidget(toolxreverse)
        
        print_action = QAction("Export", self)
        print_action.setToolTip("Save figure to file Ctrl+E")
        print_action.setShortcut('Ctrl+E')
        print_action.triggered.connect(self.canvas.export_figure)
        chartbar.addAction(print_action)
        self.addToolBar(chartbar)
        
        # creating a file menu
        file_menu = self.menuBar().addMenu("&File")
        # creating New file action
        new_file_action = QAction("New", self)
        new_file_action.setShortcut('Ctrl+N')
        # setting status tip
        new_file_action.setStatusTip("New input file")
        # adding action to the open file
        new_file_action.triggered.connect(self.file_new)
        # adding this to file menu
        file_menu.addAction(new_file_action)
        # creating an open file action
        open_file_action = QAction("Open", self)
        open_file_action.setStatusTip("Open file")
        open_file_action.setShortcut('Ctrl+O')
        open_file_action.triggered.connect(self.file_open)
        file_menu.addAction(open_file_action)
        # creating an Save file action
        save_file_action = QAction("Save", self)
        save_file_action.setStatusTip("Save file")
        save_file_action.setShortcut('Ctrl+S')
        save_file_action.triggered.connect(self.file_save)
        file_menu.addAction(save_file_action)
        # creating an Save As file action
        saveas_file_action = QAction("Save As", self)
        saveas_file_action.setStatusTip("Save file As")
        saveas_file_action.setShortcut('Ctrl+Shift+S')
        saveas_file_action.triggered.connect(self.file_saveas)
        file_menu.addAction(saveas_file_action)
        # load FID/SPE files intographics
        file_menu.addSeparator()
        load_graph_data_action = QAction("Import FID/SPE", self)
        load_graph_data_action.setShortcut('Ctrl+I')
        load_graph_data_action.setStatusTip("Load FID/SPE file to display")
        load_graph_data_action.triggered.connect(self.file_load_fidspe)
        file_menu.addAction(load_graph_data_action)
        # load test random sin wave for testing
        load_wave_data_action = QAction("Load wave", self)
        load_wave_data_action.setStatusTip("Load sin wave to display")
        load_wave_data_action.triggered.connect(self.file_load_wave)
        file_menu.addAction(load_wave_data_action)
        
        # creating a Edit menu
        edit_menu = self.menuBar().addMenu("&Edit")
        # creating Cut edit action
        cut_edit_action = QAction("Cut", self)
        cut_edit_action.setShortcut('Ctrl+X')
        cut_edit_action.setStatusTip("Cut selected text")
        cut_edit_action.triggered.connect(self.editor.cut)
        edit_menu.addAction(cut_edit_action)
        # creating Copy edit action
        copy_edit_action = QAction("Copy", self)
        copy_edit_action.setShortcut('Ctrl+C')
        copy_edit_action.setStatusTip("Copy selected text")
        copy_edit_action.triggered.connect(self.editor.copy)
        edit_menu.addAction(copy_edit_action)
        # creating Paste edit action
        paste_edit_action = QAction("Paste", self)
        paste_edit_action.setShortcut('Ctrl+V')
        paste_edit_action.setStatusTip("Paste copied text")
        paste_edit_action.triggered.connect(self.editor.paste)
        edit_menu.addAction(paste_edit_action)
        # creating Select All edit action
        selectall_edit_action = QAction("Select All", self)
        selectall_edit_action.setShortcut('Ctrl+A')
        selectall_edit_action.setStatusTip("Select All text")
        selectall_edit_action.triggered.connect(self.editor.selectAll)
        edit_menu.addAction(selectall_edit_action)
        # creating Undo edit action
        undo_edit_action = QAction("Undo", self)
        undo_edit_action.setShortcut('Ctrl+Z')
        undo_edit_action.setStatusTip("Undo last change")
        undo_edit_action.triggered.connect(self.editor.undo)
        edit_menu.addAction(undo_edit_action)
        # creating Redo edit action
        redo_edit_action = QAction("Redo", self)
        redo_edit_action.setShortcut('Ctrl+Y')
        redo_edit_action.setStatusTip("Cancel last undo action")
        redo_edit_action.triggered.connect(self.editor.redo)
        edit_menu.addAction(redo_edit_action)

        # creating a Process menu
        process_menu = self.menuBar().addMenu("&Process")
        # creating Run process action
        run_process_action = QAction("Run", self)
        run_process_action.setShortcut('Ctrl+R')
        run_process_action.setStatusTip("Execute current input")
        run_process_action.triggered.connect(self.process_run)
        process_menu.addAction(run_process_action)
        # creating Kill process action
        kill_process_action = QAction("Kill", self)
        kill_process_action.setShortcut('Ctrl+K')
        kill_process_action.setStatusTip("Kill running process")
        kill_process_action.triggered.connect(self.process_kill)
        process_menu.addAction(kill_process_action)
        # creating Clear output process action
        clearoutput_process_action = QAction("Clear output log", self)
        clearoutput_process_action.setShortcut('Ctrl+L')
        clearoutput_process_action.setStatusTip("Clear SIMPSON output window")
        clearoutput_process_action.triggered.connect(self.process_clearoutput)
        process_menu.addAction(clearoutput_process_action)

        # creating a Examples menu
        examples_menu = self.menuBar().addMenu("&Examples")
        # populating Examples with files on disk
        for examplefile in glob.glob(os.path.join(SIMPSON_EXAMPLES_PATH,"*.in")):
            examples_action = QAction(os.path.basename(examplefile), self)
            examples_action.setStatusTip("Load selected Example file")
            examples_action.triggered.connect(self.example_item_triggered)
            examples_menu.addAction(examples_action)

        # creating Chart menu
        clear_menu = self.menuBar().addMenu("&Chart")
        # creating clear selected chart item
        clear_action = QAction("Delete selected line", self)
        clear_action.setShortcut('Ctrl+D')
        clear_action.setStatusTip("Clear selected line")
        clear_action.triggered.connect(self.clear_selected)
        clear_menu.addAction(clear_action)
        # creating clear all item
        clearall_action = QAction("Delete all lines", self)
        clearall_action.setStatusTip("Clear all lines")
        clearall_action.setShortcut('Ctrl+Shift+D')
        clearall_action.triggered.connect(self.clear_all)
        clear_menu.addAction(clearall_action)

        # creating a Help menu
        help_menu = self.menuBar().addMenu("&Help")
        # help on chart
        chart_help_action = QAction("Using Chart", self)
        chart_help_action.setStatusTip("How to use Chart")
        chart_help_action.triggered.connect(self.help_chart)
        help_menu.addAction(chart_help_action)
        # help on process
        process_help_action = QAction("Using Process", self)
        process_help_action.setStatusTip("How to use Process menu")
        process_help_action.triggered.connect(self.help_process)
        help_menu.addAction(process_help_action)

        self.update_title()
        # show the whole thing up
        self.show()
                       
        
    # method to hide editor or restore previous state    
    def hideEditor(self):
        control = self.sender()
        if control.isChecked():
            # show editor
            self.mainsplitter.setSizes(self.storedMainSplitterSizes)
        else:
            # hide editor
            self.storedMainSplitterSizes = self.mainsplitter.sizes()
            self.mainsplitter.setSizes([0,1])

    # creating dialog critical method to show errors
    def dialog_critical(self, s):
        # creating a QMessageBox object
        dlg = QMessageBox(self)
        # setting text to the dlg
        dlg.setText(s)
        # setting icon to it
        dlg.setIcon(QMessageBox.Critical)
        # showing it
        dlg.show()

    # update title method
    def update_title(self):
        # setting window title with file name
        title = "SIMPSON-view: %s" %(os.path.basename(self.input_file_name) if self.input_file_name else "Untitled")
        if self.input_file_is_example:
            title = title + " EXAMPLE"
        if self.input_file_changed:
            title = title + " (*changed*)"
        self.setWindowTitle(title)
                                                   
    def editor_text_changed(self, change):
        #print("Editor trigg change:")
        #print(change)
        self.input_file_changed = change
        self.update_title()
    
    # make sure file is saved, return True if user confirms continuing (or file not changed)
    #  string tit is used to identify the caller in the message window title
    def check_file_is_saved(self, tit):
        result = True
        if self.input_file_changed:
            dlg = QMessageBox(self)
            # setting text to the dlg
            dlg.setWindowTitle(tit)
            dlg.setText("Current file is not saved. Proceed?")
            # setting icon to it
            dlg.setIcon(QMessageBox.Question)
            nobtn = dlg.addButton("No, allow saving",QMessageBox.NoRole)
            yesbtn = dlg.addButton("Yes, ignore changes",QMessageBox.YesRole)
            dlg.setDefaultButton(nobtn)
            # showing it
            dlg.exec()
            answer = dlg.clickedButton()
            if (answer == nobtn):
                #print("file not saved, stoping the action")
                result = False
            elif (answer == yesbtn):
                #print("proceed with action")
                result =  True
            else:
                #print("wrong answer, nothing done")
                result = False
        return result
            
    # editor New File        
    def file_new(self):
        #print("Triggered New File")
        # check for un-saved input file
        if self.check_file_is_saved("New File"):
            #print("new file can be loaded")
            # update path value
            self.input_file_name = None
            self.input_file_is_example = False
            # update the text
            self.editor.clear()
            self.editor_text_changed(False)
        else:
            #print("cancel new file action")
            pass
    
    def load_input_file(self,fileName,isExample=False):
        # try opening path
        try:
            with open(fileName, 'r') as f:
                # read the file
                text = f.read()
        # if some error occured
        except Exception as e:
            # show error using critical method
            self.dialog_critical(str(e))
        # else
        else:
            # update path value
            self.input_file_name = fileName
            self.input_file_is_example = isExample
            # update the text
            self.editor.setPlainText(text)
            # update the title
            self.update_title()
        
        
    # editor Open File        
    def file_open(self):
        #print("Triggered Open File")
        # check for un-saved input file
        if self.check_file_is_saved("Open File"):
            # getting path and bool value
            path, _ = QFileDialog.getOpenFileName(self, "Open file", "",
                                                  "SIMPSON input files (*.in);;All files (*.*)")
            # if path is true
            if path:
                self.load_input_file(path, isExample=False)

    # editor Save File        
    def file_save(self):
        #print("Triggered Save File")
        # if there is no save path
        if self.input_file_name is None:
            # call save as method
            return self.file_saveas()
        if self.input_file_is_example:
            self.dialog_critical("To save modified EXAMPLE use Save As")
            return
        # else call save to path method
        self.save_input_file(self.input_file_name)

    # editor Save As File        
    def file_saveas(self):
        #print("Triggered Save File As")
        # opening path
        path, _ = QFileDialog.getSaveFileName(self, "Save file", "",
                                              "SIMPSON input files (*.in);;All files (*.*)")
        # if dialog is cancelled i.e no path is selected
        if not path:
            # return this method, i.e no action performed
            return
        # else call save to path method
        self.save_input_file(path)
        
    def save_input_file(self,full_name):
        # get the text
        text = self.editor.toPlainText()
        # try catch block
        try:
            # opening file to write
            with open(full_name, 'w') as f:
                # write text in the file
                f.write(text)
                # if error occurs
        except Exception as e:
            # show error using critical
            self.dialog_critical(str(e))
        # else do this
        else:
            # change file name
            self.input_file_name = full_name
            self.input_file_changed = False
            self.editor.document().setModified(False)
            # update the title
            self.input_file_is_example = False
            self.update_title()        

    # process Run action        
    def process_run(self):
        print("Triggered Run action")
        # check for un-saved input file
        if not self.check_file_is_saved("Run SIMPSON calculation"):
            return
        # make sure we have a proper filename
        if self.input_file_name is None:
            self.dialog_critical("There is no proper input file")
            return
        if self.simpson_process is None:
            # create QProcess instance and connect slots to display output
            self.simpson_process =  QProcess() 
            self.simpson_process.readyReadStandardOutput.connect(self.handle_simpson_stdout)
            self.simpson_process.readyReadStandardError.connect(self.handle_simpson_stderr)
            self.simpson_process.finished.connect(self.handle_simpson_finished)  # Clean up once complete.
            self.simpson_process.errorOccurred.connect(self.handle_simpson_errorOccured)
            # decorations
            self.simpsonoutput.setStyleSheet("background-color: rgb(100, 255, 100)")
            usual_charformat = self.simpsonoutput.currentCharFormat()
            charformat = QTextCharFormat()
            charformat.setFontWeight(QFont.Bold)
            charformat.setFontItalic(True)
            self.simpsonoutput.setCurrentCharFormat(charformat)
            workdir, inputfile = os.path.split(self.input_file_name)
            #self.simpsonoutput.appendPlainText("Executing %s\n\n"  %inputfile)
            self.simpson_output_append("Executing %s\n"  %inputfile)
            self.simpsonoutput.setCurrentCharFormat(usual_charformat)
            self.simpson_output_append("Directory: %s\n"  %workdir)
            # execute input file
            # self.simpson_process.start("python3", ['dummy_script.py'])  # used during test phase
            self.simpson_output_append(SIMPSON_EXECUTABLE+" "+inputfile+"\n")
            env = self.simpson_process.processEnvironment()
            env.insert("TCL_LIBRARY",SIMPSON_TCL_LIBRARY)
            env.insert("LD_LIBRARY_PATH",SIMPSON_LD_LIBRARY_PATH)
            self.simpson_process.setProcessEnvironment(env)
            self.simpson_process.setWorkingDirectory(workdir)
            self.simpson_process.start(SIMPSON_EXECUTABLE, [inputfile])
        else:
            # indicate running process
            self.dialog_critical("Can not run, calculation in progress.")

    # process Clear output action        
    def process_clearoutput(self):
        # print("Triggered Clear output action")
        self.simpsonoutput.clear()

    # process Kill action        
    def process_kill(self):
        print("Triggered Kill action")
        print(self.simpson_process.state())
        if self.simpson_process is not None:
            self.simpson_process.kill() 
            print("killing")

    def simpson_output_append(self, text):
        #self.simpsonoutput.appendPlainText(text)  # adds extra end-of-line (inserts a paragraph)
        # scrollbar moves only if it is at maximum position (allows scrolling back and not moving focus when appending output)
        scrlbar = self.simpsonoutput.verticalScrollBar()
        move_scroll = ( scrlbar.value() == scrlbar.maximum() )
        self.simpsonoutput.insertPlainText(text)  # by itself, it does not handle scrollbar...
        if move_scroll:
            scrlbar.setValue(scrlbar.maximum())
     
    def handle_simpson_errorOccured(self, error):
        print("Error Occured:")
        print(error)

    def handle_simpson_stderr(self):
        # get process stderr and decode it to text
        data = self.simpson_process.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        # remember default character format
        usual_charformat = self.simpsonoutput.currentCharFormat()
        # define new character format - errors in red
        charformat = QTextCharFormat()
        charformat.setForeground(Qt.red)
        self.simpsonoutput.setCurrentCharFormat(charformat)
        # output
        self.simpson_output_append(stderr)
        # change back to default character format
        self.simpsonoutput.setCurrentCharFormat(usual_charformat)

    def handle_simpson_stdout(self):
        data = self.simpson_process.readAllStandardOutput()
        #print("stdout using str: "+str(data))
        stdout = bytes(data).decode(LOCALE_ENCODING)
        self.simpson_output_append(stdout)

    def handle_simpson_finished(self):
        print("Exit code:" , self.simpson_process.exitCode())
        print("Exit status:", self.simpson_process.exitStatus())
        usual_charformat = self.simpsonoutput.currentCharFormat()
        charformat = QTextCharFormat()
        charformat.setFontWeight(QFont.Bold)
        charformat.setFontItalic(True)
        errorstatus = (self.simpson_process.exitStatus() == QProcess.CrashExit) or ( (self.simpson_process.exitStatus() == QProcess.NormalExit) and (self.simpson_process.exitCode() != 0) )
        if errorstatus:
            charformat.setForeground(Qt.red)
            self.simpsonoutput.setCurrentCharFormat(charformat)
            self.simpson_output_append("Process crashed!\n\n")
        else:
            self.simpsonoutput.setCurrentCharFormat(charformat)
            self.simpson_output_append("Process finished.\n\n")
        self.simpsonoutput.setCurrentCharFormat(usual_charformat)
        self.simpsonoutput.setStyleSheet("background-color: rgb(255, 255, 255)")
        workdir = self.simpson_process.workingDirectory()
        #print(workdir)
        self.simpson_process = None
        # extract fidspe filename
        if not errorstatus:
            fulloutput = self.simpsonoutput.toPlainText()
            for textline in reversed(fulloutput.splitlines()):
                if textline.startswith("simview:"):
                    # remove the initial keyword and split into list of filenames
                    names = textline[len("simview:"):].strip()
                    #print(names)
                    for filename in names.split(' '):
                        fullname = os.path.join(workdir,filename)
                        #print(fullname)
                        self.load_fidspe(fullname)
                    break


    # example
    def example_item_triggered(self):
        if self.check_file_is_saved("Open Example file"):
            whichone = self.sender()
            filename = os.path.join(SIMPSON_EXAMPLES_PATH,whichone.text())
            #print("Example item selected: " + filename)
            self.load_input_file(filename, isExample=True)

    # HELP
    def help_chart(self):
        try:
            with open("help_text_chart.txt","r") as f:
                text = f.read()
        except Exception as e:
            self.dialog_critical(str(e))
            text = "No HELP text found"    
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Using Chart")
        dlg.setText(text)
        # showing it
        dlg.show()

    # HELP
    def help_process(self):
        try:
            with open("help_text_process.txt","r") as f:
                text = f.read()
        except Exception as e:
            self.dialog_critical(str(e))
            text = "No HELP text found"    
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Using Process")
        dlg.setText(text)
        # showing it
        dlg.show()

    # Clear selected line
    def clear_selected(self):
        # print("Triggered Clear Selected")
        if self.canvas.selected_line is not None:
            self.canvas.delete_simpson_data(self.canvas.selected_line)

    # Clear all lines
    def clear_all(self):
        # print("Triggered Clear All")
        self.canvas.delete_all_simpson_data()
        
    def file_load_wave(self):
        print("file_load_wave")
        t = np.linspace(0, 1)
        frq = 5*np.random.rand()
        y1 = 10*np.random.rand() * np.exp(1j*2*np.pi*t*frq)
        userdata = {'scale':1.0,'cplx_data': y1, 'show':"Real"}
        y1 = np.real(y1)
        lbl = "%.3f" % frq
        # N E E D  to handle data type FID or SPE here
        self.canvas.simpson_data_type = 'SPE'
        self.canvas.add_simpson_data(t,y1,lbl,userdata)

    def file_load_fidspe(self):
        print("file_load_fidspe")
        # getting path and bool value
        path, _ = QFileDialog.getOpenFileName(self, "Load FID/SPE", "","SIMPSON output (*.fid *.spe);;All files (*.*)")
        # if path is true
        if path:
            filename = path
        else:
            return
        self.load_fidspe(filename)
        
    def load_fidspe(self, filename):
        xx, cplx, datatype = load_simpson_fidspe(filename)
        yy = np.real(cplx)
        userdata = {'scale':1.0,'cplx_data': cplx, 'show':"Real"}
        # N E E D  to handle data type FID or SPE here
        if self.canvas.simpson_data_type is None:
            self.canvas.simpson_data_type = datatype
        else:
            if self.canvas.simpson_data_type != datatype:
                self.dialog_critical("Can't display FID and SPE together, clear the chart first")
                return
        lbl = os.path.basename(filename)
        self.canvas.add_simpson_data(xx,yy,lbl,userdata)



    def findTextHighlight(self):
        text = self.findentry.text()
        # print("Find this: '"+text+"'")
        # print(QRegExp.escape(text))
        rule = self.highlighter.highlightingRules[-1]
        if len(text) > 0:
            # print(rule[0])
            # print(rule[1])
            newrule = (QRegExp(QRegExp.escape(text)), rule[1])
        else:
            # reset the rule
            newrule = (None, rule[1])
        self.highlighter.highlightingRules[-1] = newrule 
        self.highlighter.rehighlight()


class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(Highlighter, self).__init__(parent)

        simpkeys, tclkeys = self.load_highlighter_keywords("syntax_highlight_keywords.dat")
    
        quotationFormat = QTextCharFormat()
        quotationFormat.setForeground(Qt.darkGreen)
        self.highlightingRules = [(QRegExp("\".*\""), quotationFormat)]
        
        simpsonKeywordFormat = QTextCharFormat()
        simpsonKeywordFormat.setForeground(Qt.blue)
        simpsonKeywordFormat.setFontWeight(QFont.Bold)
        for key in simpkeys:
            if len(key) != 0:
                pattern = "\\b"+key+"\\b"
                self.highlightingRules.append((QRegExp(pattern), simpsonKeywordFormat))

        tclKeywordFormat = QTextCharFormat()
        tclKeywordFormat.setForeground(Qt.darkBlue)
        tclKeywordFormat.setFontWeight(QFont.Bold)
        for key in tclkeys:
            if len(key) != 0:
                pattern = "\\b"+key+"\\b"
                self.highlightingRules.append((QRegExp(pattern), tclKeywordFormat))

        variablesFormat = QTextCharFormat()
        variablesFormat.setFontWeight(QFont.Bold)
        variablesFormat.setForeground(Qt.darkMagenta)
        self.highlightingRules.append((QRegExp(r"\$\w+"), variablesFormat))

        singleLineCommentFormat = QTextCharFormat()
        singleLineCommentFormat.setForeground(Qt.red)
        singleLineCommentFormat.setFontItalic(True)
        self.highlightingRules.append((QRegExp("#[^\n]*"), singleLineCommentFormat))

        # rule fot matching Find text MUST be the last one
        findtextFormat = QTextCharFormat()
        findtextFormat.setBackground(Qt.yellow)
        self.highlightingRules.append((None, findtextFormat))

    def load_highlighter_keywords(self, filename):
        # read in file with TCL and simpson keywords
        try:
            with open(filename, 'r') as f:
                # read the file
                text = f.read()
                keywords = text.splitlines()
                tclstart = keywords.index("[TCL_KeyWords]")
                simpstart = keywords.index("[SIMPSON_KeyWords]")
                tclkeys = keywords[(tclstart+1):simpstart]
                simpkeys = keywords[(simpstart+1):]
                # if some error occured
        except Exception as e:
            # show error using critical method and use a limited set of keywords
            print("Syntax highlighter:\n===================")
            print(str(e))
            print("--> using limited set of keywords")
            simpkeys = ["spinsys", "par", "pulse", "acq", "acq_block", "pulseid", "pulse_shaped", "delay"
                "fsimpson", "fsave", "simview", "funload", "faddlb", "fft"]
            tclkeys = ["proc", "set", "puts", "source", "global", "expr"]
        return simpkeys, tclkeys

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            if pattern is None:
                continue
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        # This part of code is related to multiline comments that does not exist in TCL
        # self.setCurrentBlockState(0)
        # startIndex = 0
        # if self.previousBlockState() != 1:
        #     startIndex = self.commentStartExpression.indexIn(text)
        # while startIndex >= 0:
        #     endIndex = self.commentEndExpression.indexIn(text, startIndex)
        #     if endIndex == -1:
        #         self.setCurrentBlockState(1)
        #         commentLength = len(text) - startIndex
        #     else:
        #         commentLength = endIndex - startIndex + self.commentEndExpression.matchedLength()
        #     self.setFormat(startIndex, commentLength,
        #             self.multiLineCommentFormat)
        #     startIndex = self.commentStartExpression.indexIn(text,
        #             startIndex + commentLength);


### G R A P H I C A L   I N T E R F A C E   P A R T
class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)

        self.mpl_connect('button_press_event', self.mButtonPress)
        self.mpl_connect('motion_notify_event', self.mMove)
        self.mpl_connect('button_release_event', self.mButtonRelease)
        self.mpl_connect('scroll_event', self.mScroll)
        self.mpl_connect('pick_event', self.legend_pick)
        # definitions from ssNAKE implementation
        self.leftMouse = False  # is the left mouse button currently pressed
        self.panX = None  # start position of dragging the spectrum
        self.panY = None  # start position of dragging the spectrum
        self.panAx = None # The ax instance from which dragging was started
        self.zoomX1 = None  # first corner of the zoombox
        self.zoomY1 = None  # first corner of the zoombox
        self.zoomX2 = None  # second corner of the zoombox
        self.zoomY2 = None  # second corner of the zoombox
        self.zoomAx = None # The ax instance from which zooming was started
        self.rect = [None, None, None, None]  # lines for zooming
        self.rightMouse = False  # is the right mouse button currently pressed
        # my definitions
        self.simpson_data_type = None  # whether we display FID or SPE
        self.legend_handle = None  # points to figure legend, used for checking empty graph
        self.selected_line = None  # index of the selected line
        self.defaultXlimits = (0,1)  # limits of full plot
        self.defaultYlimits = (0,1)  # limits of full plot
        self.pick_event_lock = False # to handle legend pick and avoid mouseButton actions on axes
        self.crosshair_cursor = None # to handle active crosshair cursor
        self.toolcursor = None  # to handle state of Crosshair checkbox
        self.toolxrev = None # to handle state of x-reverse chexkbox

    def mButtonPress(self, event):
        # print("canvas mouse event:")
        # print(event)
        if self.pick_event_lock:
            self.pick_event_lock = False;
            # print("    --> canvas action cancelled")
            return
        if (event.button == 1) and not event.dblclick :
            self.leftMouse = True
            self.zoomX1 = event.xdata
            self.zoomY1 = event.ydata
            self.zoomAx = event.inaxes
        elif event.button == 3:
            # call context menu when right-click outside axes    
            if event.inaxes is None:
                self.figure_context_menu()
            # Reset axis to default limits when double-click in axes area
            elif event.dblclick:
                self.axes.set_xlim(self.defaultXlimits)
                self.axes.set_ylim(self.defaultYlimits)
            # first righ-click in axes area prepares for panning
            else:             
                self.rightMouse = True
                self.panX = event.xdata
                self.panY = event.ydata
                self.panAx = event.inaxes

    def mMove(self, event):
        # print("canvas move:")
        # if event.inaxes is not None:
        #     print(" inside")
        # else:
        #     print("outside")
        #print(event.inaxes)
        if self.leftMouse and (self.zoomX1 is not None) and (self.zoomY1 is not None):
            # draw zooming rectangle
            inv = self.zoomAx.transData.inverted()      # convert position to axes units in case it is outside
            point = inv.transform((event.x, event.y))
            self.zoomX2 = point[0]
            self.zoomY2 = point[1]
            if self.rect[0] is not None:
                try:
                    if self.rect[0] is not None:
                        self.rect[0].remove()
                    if self.rect[1] is not None:
                        self.rect[1].remove()
                    if self.rect[2] is not None:
                        self.rect[2].remove()
                    if self.rect[3] is not None:
                        self.rect[3].remove()
                finally:
                    self.rect = [None, None, None, None]
            self.rect[0], = self.zoomAx.plot([self.zoomX1, self.zoomX2], [self.zoomY2, self.zoomY2], 'k', clip_on=False)
            self.rect[1], = self.zoomAx.plot([self.zoomX1, self.zoomX2], [self.zoomY1, self.zoomY1], 'k', clip_on=False)
            self.rect[2], = self.zoomAx.plot([self.zoomX1, self.zoomX1], [self.zoomY1, self.zoomY2], 'k', clip_on=False)
            self.rect[3], = self.zoomAx.plot([self.zoomX2, self.zoomX2], [self.zoomY1, self.zoomY2], 'k', clip_on=False)
            if event.inaxes is None:
                # rectangle gets outside the current axes -> enlarge them
                xlim = self.axes.get_xlim()
                ylim = self.axes.get_ylim()
                if (self.toolxrev.isChecked()):
                    xminlim = max([self.zoomX1, self.zoomX2, xlim[0]])
                    xmaxlim = min([self.zoomX1, self.zoomX2, xlim[1]])
                else:
                    xminlim = min([self.zoomX1, self.zoomX2, xlim[0]])
                    xmaxlim = max([self.zoomX1, self.zoomX2, xlim[1]])
                yminlim = min([self.zoomY1, self.zoomY2, ylim[0]])
                ymaxlim = max([self.zoomY1, self.zoomY2, ylim[1]])
                self.axes.set_xlim(xminlim, xmaxlim) 
                self.axes.set_ylim(yminlim, ymaxlim)               
            self.draw_idle()
        elif self.rightMouse and self.panX is not None and self.panY is not None:
            # pan feature
            inv = self.panAx.transData.inverted()      # convert position to axes units in case it is outside
            point = inv.transform((event.x, event.y))
            diffx = self.panX - point[0]
            diffy = self.panY - point[1]
            xlim = self.axes.get_xlim()
            ylim = self.axes.get_ylim()
            self.axes.set_xlim(xlim[0]+diffx,xlim[1]+diffx)
            self.axes.set_ylim(ylim[0]+diffy,ylim[1]+diffy)
            self.draw_idle()
            
    def mButtonRelease(self, event):
        # print("mouse released")
        # print(event)
        if event.button == 1:
            # finish zooming and reset zooming data in self
            self.leftMouse = False
            try:
                if self.rect[0] is not None:
                    self.rect[0].remove()
                if self.rect[1] is not None:
                    self.rect[1].remove()
                if self.rect[2] is not None:
                    self.rect[2].remove()
                if self.rect[3] is not None:
                    self.rect[3].remove()
            finally:
                self.rect = [None, None, None, None]
            if self.zoomX2 is not None and self.zoomY2 is not None:                    
                xminlim = min([self.zoomX1, self.zoomX2])
                xmaxlim = max([self.zoomX1, self.zoomX2])
                yminlim = min([self.zoomY1, self.zoomY2])
                ymaxlim = max([self.zoomY1, self.zoomY2])
                if (xmaxlim-xminlim>1e-12) and (ymaxlim-yminlim>1e-12):
                    #self.axes.set_xlim(xminlim, xmaxlim)
                    if (self.toolxrev.isChecked()): 
                        self.axes.set_xlim(xmaxlim, xminlim)
                    else: 
                        self.axes.set_xlim(xminlim, xmaxlim) 
                    self.axes.set_ylim(yminlim, ymaxlim)
            self.zoomX1 = None
            self.zoomX2 = None
            self.zoomY1 = None
            self.zoomY2 = None
        elif event.button == 3:
            # stop panning
            self.rightMouse = False
        self.draw_idle()

    def mScroll(self, event):
        if event.inaxes is None:
            return
        scale = 0.9**event.step
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ShiftModifier:
            # scaling x-axis
            xlim = self.axes.get_xlim()
            pos_x = event.xdata
            xminlim = pos_x - scale*(pos_x-xlim[0])
            xmaxlim = pos_x + scale*(xlim[1]-pos_x)
            self.axes.set_xlim(xminlim, xmaxlim)
        else:
            if self.selected_line is not None:
                # scaling selected line data
                #print("scaling selected line %d by %g" % (self.selected_line, scale) )
                plotlines =  self.get_plotlines()
                line = plotlines[self.selected_line]
                yynew = line.get_ydata()*scale
                line.user_data['scale'] = line.user_data['scale']*scale
                line.set_ydata(yynew)
                # pass line data to snapped cursor to the selected line
                self.snapped_cursor_update()
            else:
                # scaling y-axis
                ylim = self.axes.get_ylim()
                pos_y = event.ydata
                yminlim = pos_y - scale*(pos_y-ylim[0])
                ymaxlim = pos_y + scale*(ylim[1]-pos_y)
                self.axes.set_ylim(yminlim, ymaxlim)
        self.draw_idle()
        # print("scrolling:")
        # print(event.step)

    # pass line data to snapped cursor to the selected line
    def snapped_cursor_update(self):
        if (self.crosshair_cursor is not None):
            if (self.selected_line is None):
                self.crosshair_cursor.xx = None
                self.crosshair_cursor.yy = None
            else: 
                plotlines = self.get_plotlines()
                self.crosshair_cursor.xx, self.crosshair_cursor.yy = plotlines[self.selected_line].get_data()

    # add simpson data
    def add_simpson_data(self, xdata , ydata, datalabel, userdata):
        # xdata, ydata to display in Chart using plot
        # datalabel to be displayed in legend
        if self.legend_handle is None:
            # this is the first plot
            newline = self.axes.plot(xdata, ydata, lw=1, label=datalabel)
            self.axes.relim()
            self.axes.autoscale()
            # remember these axes limits
            self.defaultXlimits = self.axes.get_xlim()
            self.defaultYlimits = self.axes.get_ylim()
            if self.simpson_data_type == 'SPE':
                self.axes.set_xlabel('frequency [Hz]')
            elif self.simpson_data_type == 'FID':
                self.axes.set_xlabel('time [ms]')
        else:
            # additional lines
            # remember current axes limits
            xlims = self.axes.get_xlim()
            ylims = self.axes.get_ylim()
            #print("original limits:",xlims,ylims)
            # plot additional line
            newline = self.axes.plot(xdata, ydata, lw=1, label=datalabel)
            # recalculate axes limits and store them as default (should capture all data lines)
            self.axes.relim()
            self.axes.autoscale()
            self.defaultXlimits = self.axes.get_xlim()
            self.defaultYlimits = self.axes.get_ylim()
            #print("relim limits:",self.defaultXlimits,self.defaultYlimits)
            # restore current zoom
            self.axes.set_xlim(xlims)
            self.axes.set_ylim(ylims)
        # update legend and pick properties
        newline[0].user_data = userdata
        self.update_legend()
        self.draw_idle()
        
    # delete simpson data from the plot using their plot-line index    
    def delete_simpson_data(self, idx):
        # plotlines = self.axes.get_lines()
        plotlines = self.get_plotlines()
        if self.selected_line == idx:
            self.selected_line = None
            if self.crosshair_cursor is not None:
                self.crosshair_cursor.xx = None
                self.crosshair_cursor.yy = None
        # remember current axes limits
        xlims = self.axes.get_xlim()
        ylims = self.axes.get_ylim()
        plotlines[idx].remove()
        # recalculate axes limits and store them as default (should capture all data lines)
        self.axes.relim()
        self.axes.autoscale()
        self.defaultXlimits = self.axes.get_xlim()
        self.defaultYlimits = self.axes.get_ylim()
        # restore current zoom
        self.axes.set_xlim(xlims)
        self.axes.set_ylim(ylims)
        # redraw
        self.update_legend()
        self.draw_idle()
        
    def delete_all_simpson_data(self):
        plotlines = self.get_plotlines()
        self.selected_line = None
        if self.crosshair_cursor is not None:
            self.crosshair_cursor.xx = None
            self.crosshair_cursor.yy = None
        for pl in plotlines:
            pl.remove()
        self.update_legend()
        # print("remove all - lims are: ",self.defaultXlimits,self.defaultXlimits)
        self.axes.set_prop_cycle(None)
        self.draw_idle()
        
        
    # extract list of lines in current plot except crosshair-cursor lines (without a label)
    def get_plotlines(self):
        plotlines =  self.axes.get_lines()
        # print("get plot lines count = ",len(plotlines))
        datalines = []
        for ln in plotlines:
            # print("line label: ",ln.get_label())
            if ln.get_label() == '__cursor__':
                continue
            datalines.append(ln)
        return datalines
        
    def update_legend(self):
        #plotlines = self.axes.get_lines()
        plotlines = self.get_plotlines()
        # print(" update legend number of plot lines: ",len(plotlines))
        if len(plotlines) == 0:
            self.legend_handle.remove()
            self.legend_handle = None
            # self.defaultXlimits = (0,1)
            self.defaultXlimits = (0,1) if not self.toolxrev.isChecked() else (1,0)
            self.defaultYlimits = (0,1)
            self.axes.set_xlim(self.defaultXlimits)
            self.axes.set_ylim(self.defaultYlimits)
            self.simpson_data_type = None
            self.axes.set_xlabel('')
            return
        legendhandle = self.axes.legend(loc='upper right', fancybox=True, shadow=True)
        self.legend_handle = legendhandle
        leglines = legendhandle.get_lines()
        legtexts = legendhandle.get_texts()
        # print(" update legend number of legend lines: ",len(leglines))
        for idx in range(len(plotlines)):
            # print("legend update idx = ",idx)
            leglines[idx].set_picker(True) 
            legtexts[idx].set_picker(True)
            if plotlines[idx].get_visible() is False:
                leglines[idx].set_visible(True)
                leglines[idx].set_alpha(0.2)
            if idx == self.selected_line:
                legtexts[idx].set_text("*"+plotlines[idx].get_label())
    
    # handle mouse clicks on legend
    def legend_pick(self, event):
        self.pick_event_lock = True
        # print("legend pick event button: ",event.mouseevent.button)
        leglines = self.legend_handle.get_lines()
        plotlines = self.get_plotlines()
        textlines = self.legend_handle.get_texts()
        if event.mouseevent.button == 1:
            # print("  --> left")
            if isinstance(event.artist, matplotlib.lines.Line2D):
                # toggle line invisible
                legendline = event.artist
                # leglines = self.legend_handle.get_lines()
                # plotlines = self.axes.get_lines()
                idx = leglines.index(legendline)
                visible = not plotlines[idx].get_visible()
                plotlines[idx].set_visible(visible)
                legendline.set_alpha(1.0 if visible else 0.2)
                self.draw_idle()
            elif isinstance(event.artist, matplotlib.text.Text):
                # toggle selected line
                legendtext = event.artist
                # leglines = self.legend_handle.get_lines()
                # textlines = self.legend_handle.get_texts()
                # plotlines = self.axes.get_lines()
                idx = textlines.index(legendtext)
                if idx == self.selected_line:
                    self.selected_line = None
                    legendtext.set_text(plotlines[idx].get_label())                    
                else:
                    if self.selected_line is not None:
                        textlines[self.selected_line].set_text(plotlines[self.selected_line].get_label())
                    self.selected_line = idx
                    legendtext.set_text("*"+plotlines[idx].get_label())
                # print("Text legend number:" + str(idx))
                # print("     selected :", self.selected_line)
                # pass line data to snapped cursor to the selected line
                self.snapped_cursor_update()
                #if (self.crosshair_cursor is not None):
                #    if (self.selected_line is None):
                #        self.crosshair_cursor.xx = None
                #        self.crosshair_cursor.yy = None
                #    else: 
                #        self.crosshair_cursor.xx, self.crosshair_cursor.yy = plotlines[self.selected_line].get_data()
        elif event.mouseevent.button == 3:
            # print("  --> right")
            if isinstance(event.artist, matplotlib.lines.Line2D):
                # start line editing menu???
                print("right action on line")
            elif isinstance(event.artist, matplotlib.text.Text):
                # delete line
                # print("right action on text")
                idx = textlines.index(event.artist)
                msg = "Delete " + plotlines[idx].get_label() + "?" 
                # + str(plotlines[idx].user_data['scale'])
                menu = QMenu()
                ActDelete = menu.addAction(msg)
                ActScale = menu.addAction("Set scale")
                ActReIm = menu.addAction("Toggle Real/Imag")
                action = menu.exec(QCursor.pos())
                if action == ActDelete:
                    # print("Deleting")
                    self.delete_simpson_data(idx)
                elif action == ActScale:
                    # print("manege scale ")
                    self.set_line_scaling(idx)
                elif action == ActReIm:
                    self.toggle_reim(idx)
                else:
                    # print("canceling")
                    pass
    
    # set scaling of individual line in plot
    def set_line_scaling(self, idx):
        #print("manege scale of line %d" % idx)
        plotlines = self.get_plotlines()
        line = plotlines[idx]
        yy = line.get_ydata()
        # remove previous scaling
        scale1 = line.user_data['scale']
        yy = yy/scale1
        # get new scaling factor
        #scale2, completed = QInputDialog.getDouble(self, 'Line scaling', 'Enter new scaling factor:', scale1)
        # the line above does the same as the following 7 lines, except here I can set Locale for decimal point (and not decimal comma as for czech locale...)
        dlg = QInputDialog()
        dlg.setWindowTitle('Line scaling');
        dlg.setInputMode(QInputDialog.DoubleInput)
        dlg.setLabelText('Enter new scaling factor: ')
        dlg.setDoubleRange(-1e12, 1e12)  # practically unlimited upper bound
        #spin_box = dlg.findChild(QDoubleSpinBox)
        #if spin_box:
        #    spin_box.setDecimals(6)  # allow up to 6 decimal places
        dlg.setDoubleValue(scale1)
        dlg.setLocale(QLocale(QLocale.English,QLocale.UnitedKingdom))
        completed = dlg.exec()
        # print(completed)
        if not completed:
            scale2 = scale1
        else:
            scale2 = dlg.doubleValue()
        # apply new scaling
        line.user_data['scale'] = scale2
        yy = yy*scale2
        line.set_ydata(yy)
        # pass line data to snapped cursor to the selected line
        self.snapped_cursor_update()
        #if (self.crosshair_cursor is not None):
        #    if (self.selected_line is None):
        #        self.crosshair_cursor.xx = None
        #        self.crosshair_cursor.yy = None
        #    else: 
        #         self.crosshair_cursor.xx, self.crosshair_cursor.yy = plotlines[self.selected_line].get_data()
        # update figure
        self.draw_idle()

    # toggle if line shows real or imaginary part
    def toggle_reim(self, idx):
        print("toggle real / imag")
        items = ["Real", "Imag"]
        plotlines = self.get_plotlines()
        line = plotlines[idx]
        current = line.user_data['show']
        item, ok = ListSelectionDialog().getItem(self,"Toggle Re/Im","Real or Imag?:", items, current)
        if ok:
            print("toggle re /im succsess")
            if item == "Real":
                yy = np.real(line.user_data['cplx_data']) * line.user_data['scale']
                line.user_data['show'] = "Real"
            else:
                yy = np.imag(line.user_data['cplx_data']) * line.user_data['scale']
                line.user_data['show'] = "Imag"
            line.set_ydata(yy)
            self.snapped_cursor_update()
            self.draw_idle()
    
    # figure context menu activated by right-click outside axes
    def figure_context_menu(self):
        menu = QMenu()
        export_action = QAction("Export figure", self)
        export_action.triggered.connect(self.export_figure)
        menu.addAction(export_action)
        edit_action = QAction("Edit figure", self)
        edit_action.triggered.connect(self.edit_figure)
        menu.addAction(edit_action)
        crosshair_action = QAction("Crosshair cursor", self)
        crosshair_action.triggered.connect(self.handle_crosshair_cursor)
        menu.addAction(crosshair_action)
        #xrev_action = QAction("Reverse x-axis", self)
        #xrev_action.triggered.connect(self.handle_xrev)
        #menu.addAction(xrev_action)
        menu.exec(QCursor.pos())

    def addToolcursor(self, tc):
        self.toolcursor = tc
        
    def addToolxrev(self, xrev):
        self.toolxrev = xrev
        
    def handle_crosshair_cursor(self):
        if self.crosshair_cursor is None:
            # start crusror regime
            # print("cursor ON")
            cursor = Cursor(self.axes) # Cursor does mpl_connect during __init__  
            if (self.selected_line is not None):
                plotlines = self.get_plotlines()
                cursor.xx, cursor.yy = plotlines[self.selected_line].get_data()
            self.crosshair_cursor = cursor
            self.toolcursor.setChecked(True)
        else:
            # cancel cursor regime (destructor of cursor)
            # print("cursor OFF")
            # self.crosshair_cursor.horizontal_line.remove()
            # self.crosshair_cursor.vertical_line.remove()
            # self.crosshair_cursor.text.remove()
            # self.mpl_disconnect(self.crosshair_cursor.cid)
            self.crosshair_cursor.remove_internals()
            self.crosshair_cursor = None
            self.toolcursor.setChecked(False)
        
    def handle_xrev(self):
        if (self.toolxrev.isChecked()): 
            #print("revx not compatible with zoom and other things...")
            self.axes.xaxis.set_inverted(True)
            self.defaultXlimits = tuple(sorted(self.defaultXlimits, reverse=True))
        else:
            self.axes.xaxis.set_inverted(False)
            self.defaultXlimits = tuple(sorted(self.defaultXlimits))
        # update figure
        self.draw_idle()    

    def export_figure(self):
        print("save figure to file")
        # ask filename
        filename, _ = QFileDialog.getSaveFileName(self, "Export figure", "","(*.png *.pdf *.svg  *.eps *.jpg)")
        # if dialog is cancelled i.e no path is selected
        if not filename:
            # return this method, i.e no action performed
            return
        # else call save to path method
        self.fig.savefig(filename)
        
    def edit_figure(self):
        print("edit figure properties not implemented")

class Cursor:
    """
    A cross hair cursor.
    """
    def __init__(self, ax):
        self.ax = ax
        self.horizontal_line = ax.axhline(color='k', lw=0.8, ls='--', label='__cursor__')
        self.vertical_line = ax.axvline(color='k', lw=0.8, ls='--', label='__cursor__')
        # text location in axes coordinates
        self.text = ax.text(0.02, 0.95, '', transform=ax.transAxes, bbox=dict(facecolor='red', alpha=0.5))
        # line data used for snapped cursor mode (when a line is selected)
        self.xx = None
        self.yy = None
        self.lastindex = None
        # distance measurements activated by left click
        self.position_origin = None
        # connected action slot ID
        cid = self.ax.figure.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.cid = [cid]
        cid = self.ax.figure.canvas.mpl_connect('button_press_event', self.on_mouse_button)
        self.cid.append(cid)
        # cid = self.ax.figure.canvas.mpl_connect('button_release_event', self.off_mouse_button)
        # self.cid.append(cid) 
        self.position_origin_horizontal_line = None
        self.position_origin_vertical_line = None
        self.position_delta_text = None

    def remove_internals(self):
        self.horizontal_line.remove()
        self.vertical_line.remove()
        self.text.remove()
        if self.position_origin_horizontal_line is not None:
            self.position_origin_horizontal_line.remove()
            self.position_origin_vertical_line.remove()
            self.position_delta_text.remove()
            self.ax.figure.canvas.draw()
        for cid in self.cid:
            self.ax.figure.canvas.mpl_disconnect(cid)
        
    # def off_mouse_button(self,event):
    #     print("cursor mouse released: ",event)
    #     if (event.button == 1) and event.dblclick:
    #         print("  -- Hught -- ")
            
    def on_mouse_button(self, event):
        if (event.button == 1) and event.dblclick and (event.inaxes is not None):
            if self.position_origin is None:
                if (self.lastindex is not None) and (self.xx is not None):
                    x = self.xx[self.lastindex]
                    y = self.yy[self.lastindex]
                else:
                    x = event.xdata
                    y = event.ydata
                self.position_origin = (x, y)
                self.position_origin_horizontal_line = self.ax.axhline(y=y, color='k', lw=0.8, ls='--', label='__cursor__')
                self.position_origin_vertical_line = self.ax.axvline(x=x, color='k', lw=0.8, ls='--', label='__cursor__')
                self.position_delta_text = self.ax.text(x, y, ' dx=0, dy=0', verticalalignment='bottom')
            else:
                self.position_origin = None
                self.position_origin_horizontal_line.remove()
                self.position_origin_vertical_line.remove()
                self.position_delta_text.remove()
                self.position_origin_horizontal_line = None
                self.position_origin_vertical_line = None
                self.position_delta_text = None
                self.ax.figure.canvas.draw()
            # print(" pos orig: ",self.position_origin)
        
        
    def set_cross_hair_visible(self, visible):
        need_redraw = self.horizontal_line.get_visible() != visible
        self.horizontal_line.set_visible(visible)
        self.vertical_line.set_visible(visible)
        self.text.set_visible(visible)
        return need_redraw

    def on_mouse_move(self, event):
        if not event.inaxes:
            need_redraw = self.set_cross_hair_visible(False)
            if need_redraw:
                self.ax.figure.canvas.draw()
        else:
            self.set_cross_hair_visible(True)
            x, y = event.xdata, event.ydata
            # update the line positions
            if self.xx is not None:
                # snapped version
                index = min(np.searchsorted(self.xx, x), len(self.xx) - 1)
                if index == self.lastindex: # do not move the cursor
                    return
                self.lastindex = index
                x = self.xx[index]
                y = self.yy[index]
            else:
                self.lastindex = None
            # general version
            self.horizontal_line.set_ydata([y])
            self.vertical_line.set_xdata([x])
            if self.position_origin is None:
                self.text.set_text('x=%1.2f, y=%1.2f' % (x, y))
            else:
                dx = x - self.position_origin[0] 
                dy = y - self.position_origin[1]
                self.position_delta_text.set_text(' dx=%1.2f, dy=%1.2f' % (dx, dy))
                self.position_delta_text.set_position((x,y))
            self.ax.figure.canvas.draw()

### L O A D I N G   FID / SPE   D A T A   P A R T
def load_simpson_fidspe(fileName):
    # ordinary ASCII fid or spe, need to calculate x-coordinate, y is just real part     
    try:
        with open(fileName, 'r') as file:
            # check the first line for SIMP
            line =  file.readline()
            line.strip()
            if line[:-1] != "SIMP":
                print("Not simpson file:")
                print(fileName)
            else:
                #print("is simp file")
                pass
    
            # read the file
            info = {}
            for line in file:
                line.strip()
                line = line[:-1]
                if line == "DATA":
                    # data start here
                    break
                else:
                    # read header
                    ll = line.split("=")
                    #print("Line >"+line+"< is ",ll)
                    info[ll[0]]=ll[1]
            #print(info)
            cplx = []
            if 'NP' in info:
                info['NP'] = int(info['NP'])
            else:
                print("Error: NP not found")
            if 'SW' in info:
                info['SW'] = float(info['SW'])
            else:
                print("Error: SW not found")
            if 'REF' in info:
                info['REF'] = float(info['REF'])
            else:
                info['REF'] = 0
            for i in range(0,info['NP']):
                line = file.readline()
                line.strip()
                line = line[:-1]
                x,y = [float(i) for i in line.split()]
                cplx.append(complex(x,y))
            file.close()            
    # if some error occured
    except Exception as e:
        # show error using critical method
        #self.dialog_critical(str(e))
        print(str(e))
    # else
    else:
        # update path value
        # print("Lines: ",len(text))
        # for i in range(1,10):
        #     print("   ",text[i])
        #print(info)
        # create x axis
        if info['TYPE'] == "SPE":
            corr = info['SW']/2-info['REF']
            stx = info['SW']/(info['NP']-1)
        elif info['TYPE'] == "FID":
            stx = 1.0e3/info['SW']
            corr = 0
        else:
            print("Error: unknown TYPE ",info['TYPE'])
        xx = [i*stx-corr for i in range(0,len(cplx))] #this must be repaired  
        datatype = info['TYPE']
    return xx, cplx, datatype

# Nice dialog for selection from list, all items visible
class ListSelectionDialog(QDialog):
    def __init__(self, parent=None, title="Select Item", question="", items=None, current_item=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.choice = None
        items = items or []

        layout = QVBoxLayout()
        # Optional question label
        if question:
            self.label = QLabel(question)
            self.label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.label)
        # List widget
        self.list_widget = QListWidget()
        self.list_widget.addItems(items)
        layout.addWidget(self.list_widget, alignment=Qt.AlignCenter)
        # adjust its sizes
        item_count = self.list_widget.count()
        height = self.list_widget.sizeHintForRow(0)*item_count + 2*self.list_widget.frameWidth() + 4 # extra padding
        width = 0
        for i in range(item_count):
            item_width = self.list_widget.sizeHintForIndex(self.list_widget.model().index(i, 0)).width()
            width = max(width, item_width)
        width = width + 2 * self.list_widget.frameWidth() + 20 # padding + scrollbar space
        self.list_widget.setFixedSize(width, height) 
        # Preselect item if specified
        if current_item and current_item in items:
            index = items.index(current_item)
            self.list_widget.setCurrentRow(index)
        elif items:
            self.list_widget.setCurrentRow(0)
        # Push OK button
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.confirm_selection)
        layout.addWidget(self.ok_button, alignment=Qt.AlignCenter)
        # finish the dialog
        self.setLayout(layout)
        self.setWindowModality(Qt.ApplicationModal)        

    def confirm_selection(self):
        item = self.list_widget.currentItem()
        if item:
            self.choice = item.text()
        self.accept()  # closes the dialog

    @staticmethod
    def getItem(parent=None, title="Select Item", question="", items=None, current_item=None):
        dialog = ListSelectionDialog(parent, title, question, items, current_item)
        result = dialog.exec_()
        return (dialog.choice, result == QDialog.Accepted)


# execute the thing
if __name__ == '__main__':

    # creating PyQt5 application
    app = QApplication(sys.argv)
    # setting application name
    app.setApplicationName("SIMPSON-view")
    # creating a main window object
    window = MainWindow()
    # loop
    sys.exit(app.exec())

