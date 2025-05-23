# -*- coding: utf-8 -*-
"""
Created on Wed Jul  6 14:05:04 2022

@author: Mingeon Kim, CT/MI Research Collaboration Scientist, SIEMENS Healthineers, Korea
"""


import pydicom, numpy as np
import pydicom._storage_sopclass_uids
from pydicom.uid import generate_uid
import hmac
import binascii
import hashlib

import os
import tkinter.ttk as ttk
import tkinter.messagebox as msgbox
from tkinter import * # __all__
from tkinter import filedialog



root = Tk()
root.title("SIEMENS Healthineers Korea - DE Mix Data Generator")

def add_file():
    files = filedialog.askdirectory(title="추가할 파일경로를 선택하세요", \
        initialdir=r".\Desktop")
        # 최초에 사용자가 지정한 경로를 보여줌

    # 사용자가 선택한 파일 목록
    list_file.insert(END, files)

# 선택 삭제
def del_file():
    #print(list_file.curselection())
    for index in reversed(list_file.curselection()):
        list_file.delete(index)


# 추사 경로 (폴더)
def browse_dest_loadpath():
    folder_selected = filedialog.askdirectory()
    if folder_selected == "": # 사용자가 취소를 누를 때
        # print("폴더 선택 취소")
        return
    #print(folder_selected)
    txt_dest_loadpath.delete(0, END)
    txt_dest_loadpath.insert(0, folder_selected)


    
def hash_acc(num, length, sideID):
   try:
       siteID = str.encode(sideID)
       num = str.encode(num)
                              # hash
       m = hmac.new(siteID, num, hashlib.sha256).digest()
                              #convert to dec
       m = str(int(binascii.hexlify(m),16))
                              #split till length
       m=m[:length]
       return m
   except Exception as e:
          print("Something went wrong hashing a value :(")
          return
      
        
def dicom_reader(folder, images_path):
    
    path_tmp = []
    name_tmp = []
    
    for (path, dir, files) in os.walk(images_path + "/" + folder):
        for filename in files:
            ext = os.path.splitext(filename)[-1]
        
            if ext == '.dcm' or '.IMA':
                print("%s/%s" % (path, filename))
                path_tmp.append(path)
                name_tmp.append(filename)
                               
    dcm_tmp = []

    for i in range(len(path_tmp)):
        dcm_p = pydicom.dcmread(path_tmp[i] + '/' + name_tmp[i], force = True)
        dcm_tmp.append(dcm_p)
    
    insertion_sort_time(dcm_tmp)
    
    img_tmp = []
    
    for ii in range(len(dcm_tmp)):
        ccc = dcm_tmp[ii].pixel_array
        img_tmp.append(ccc)

    return path_tmp, name_tmp, img_tmp, dcm_tmp

def insertion_sort_time(my_list):# 삽입 정렬
    for i in range(len(my_list)):
        key = my_list[i]

        # i - 1부터 시작해서 왼쪽으로 하나씩 확인
        # 왼쪽 끝까지(0번 인덱스) 다 봤거나
        # key가 들어갈 자리를 찾으면 끝냄
        j = i - 1
        while j >= 0 and my_list[j].AcquisitionTime > key.AcquisitionTime:
            my_list[j + 1] = my_list[j]
            j = j - 1

        # key가 들어갈 자리에 삽입
        # 왼쪽 끝까지 가서 j가 -1이면 0번 인덱스에 key를 삽입
        my_list[j + 1] = key


def insertion_sort_position(my_list):# 삽입 정렬
    for i in range(len(my_list)):
        key = my_list[i]

        # i - 1부터 시작해서 왼쪽으로 하나씩 확인
        # 왼쪽 끝까지(0번 인덱스) 다 봤거나
        # key가 들어갈 자리를 찾으면 끝냄
        j = i - 1
        while j >= 0 and my_list[j].ImagePositionPatient[2] > key.ImagePositionPatient[2]:
            my_list[j + 1] = my_list[j]
            j = j - 1

        # key가 들어갈 자리에 삽입
        # 왼쪽 끝까지 가서 j가 -1이면 0번 인덱스에 key를 삽입
        my_list[j + 1] = key

def replace_uid_suffix(original_uid, new_suffix):
    """
    UID 접두는 그대로 두고, 마지막 . 이후 부분을 새 suffix로 바꿈
    """
    parts = original_uid.split('.')
    parts[-1] = new_suffix
    return '.'.join(parts)


def DEMixer(images_path, low_ratio, high_ratio, low_path, low_name, low_img, low_dcm, high_path, high_name, high_img, high_dcm):   
    # metadata
    fileMeta = pydicom.Dataset()
    fileMeta.MediaStorageSOPClassUID = pydicom._storage_sopclass_uids.CTImageStorage
    fileMeta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    fileMeta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
    
  
    idx = 0
    mixed_img = []
    new_series_suffix = generate_uid().split('.')[-1]
    for idx in range(len(low_dcm)):
        
        low_hu = low_img[idx] * low_dcm[idx].RescaleSlope + low_dcm[idx].RescaleIntercept
        high_hu = high_img[idx] * high_dcm[idx].RescaleSlope + high_dcm[idx].RescaleIntercept

    # mixing (float 연산)
        mix_hu = low_hu * low_ratio + high_hu * high_ratio

    # 다시 raw pixel 값으로 변환 (역변환)
        rescale_slope = 1
        rescale_intercept = -1024
        mix_raw = (mix_hu - rescale_intercept) / rescale_slope
        mix_raw = np.clip(mix_raw, 0, 4095).astype(np.int16)  # unsigned일 경우 0~4095
        
        mixed_img.append(mix_raw)
        
        
        low_dcm[idx].file_meta = fileMeta
        low_dcm[idx].SeriesDescription = "DEMixedimg_low" + str(low_ratio * 100) + "%_+_high" + str(high_ratio * 100) +"%"
        low_dcm[idx].BitsAllocated = 16
        low_dcm[idx].PixelRepresentation = 0
        low_dcm[idx].PixelData = mix_raw.tobytes()
        low_dcm[idx].SeriesInstanceUID = replace_uid_suffix(low_dcm[idx].SeriesInstanceUID, new_series_suffix)  # 새 UID 자동 생성
        low_dcm[idx].SeriesNumber = 1001  # 원하는 숫자 입력
        new_SOP_suffix = generate_uid().split('.')[-1]
        low_dcm[idx].SOPInstanceUID = replace_uid_suffix(low_dcm[idx].SOPInstanceUID, new_SOP_suffix)  # 새 UID 자동 생성
        
        
        savedir = os.path.join(images_path +'/Mixed_low(' + str(low_ratio) +')_+_high(' + str(high_ratio) +')')
        if not(os.path.exists(savedir)):
            os.makedirs(savedir)
        
        low_dcm[idx].save_as(savedir + '/DE_Mixed_' + str(low_name[idx]), write_like_original=False)
        
        progress = idx / len(low_dcm) * 100 # 실제 percent 정보를 계산
        p_var.set(progress)
        progress_bar.update()
        
        
    return print("DE mixed 영상처리가 완료되었습니다." + str(savedir) + "을 확인해주세요!")

def Mixed(images_path):
    try:
        low_path, low_name, low_img, low_dcm = dicom_reader("low", images_path)
        high_path, high_name, high_img, high_dcm = dicom_reader("high", images_path)
        
        low_ratio = float(txt_studynumb.get())
        high_ratio = float(txt_studyname.get())

        DEMixer(images_path, low_ratio, high_ratio, low_path, low_name, low_img, low_dcm, high_path, high_name, high_img, high_dcm)
        
        
            
    except Exception as err: # 예외처리
        msgbox.showerror("에러", err + ", Research Scientist에게 문의해주세요!")
        
        
        
'''
shutil.rmtree(r"path")
'''      

# 시작
def start():
    # 각 옵션들 값을 확인
    # print("가로넓이 : ", cmb_width.get())
    # print("간격 : ", cmb_space.get())
    # print("포맷 : ", cmb_format.get())

    # 파일 목록 확인
    if list_file.size() == 0:
        msgbox.showwarning("경고", "폴더 경로를 추가해주세요")
        return
    
    # 이미지 통합 작업
    

    images_path = list_file.get(0, END)
    print(images_path)

    
    for i_n in range(len(images_path)):
        Mixed(images_path[i_n])
        
    msgbox.showinfo("알림", "데이터 생성이 완료되었습니다~ 추가하신 폴더 안을 확인해주세요.")  


photo = PhotoImage(file="./pics/siemens.png")
label2 = Label(root, image=photo)
label2.pack()

# 파일 프레임 (파일 추가, 선택 삭제)
file_frame = LabelFrame(root, text="Dual Energy 폴더 2개가 포함된 상위폴더를 추가해주세요!")
file_frame.pack(fill="x", padx=10, pady=5, ipadx = 5) # 간격 띄우기

btn_add_file = Button(file_frame, padx=5, pady=5, width=25, text="폴더추가", command=add_file)
btn_add_file.pack(side="left")

btn_del_file = Button(file_frame, padx=5, pady=5, width=25, text="선택삭제", command=del_file)
btn_del_file.pack(side="right")

# 리스트 프레임
list_frame = Frame(root)
list_frame.pack(fill="both", padx=5, pady=5)

scrollbar = Scrollbar(list_frame)
scrollbar.pack(side="right", fill="y")

list_file = Listbox(list_frame, selectmode="extended", height=5, yscrollcommand=scrollbar.set)
list_file.pack(side="left", fill="both", expand=True)
scrollbar.config(command=list_file.yview)


# btn_dest_savepath.pack(side="right", padx=5, pady=5)

# 옵션 프레임
frame_option = LabelFrame(root, text="Mixed ratio를 각각 입력해주세요!")
frame_option.pack(padx=15, pady=15, ipadx = 5, ipady=5)
################################################################



# Study number 옵션
lbl_studynumb = Label(frame_option, text="Low_kVp ratio: ", width = 15)
lbl_studynumb.pack(side="left", padx = 5, pady = 5, fill="both", expand=True)

txt_studynumb = Entry(frame_option, width=5)
txt_studynumb.pack(side = "left", padx = 0, pady = 5)
txt_studynumb.insert(END, "0.4")

txt_studyname = Entry(frame_option, width=5)
txt_studyname.pack(side = "right", padx = 10, pady = 5)
txt_studyname.insert(END, "0.6")

# 익명화 이름 옵션
lbl_studyname = Label(frame_option, text="*    High_kVp ratio: ", width = 15)
lbl_studyname.pack(side="right", padx = 5, pady = 5, ipadx = 5, fill="both", expand=True)



##################################################################
# 진행 상황 Progress Bar
frame_progress = LabelFrame(root, text="진행상황")
frame_progress.pack(fill="x", padx=5, pady=5, ipady=5)

p_var = DoubleVar()
progress_bar = ttk.Progressbar(frame_progress, maximum=100, variable=p_var)
progress_bar.pack(fill="x", padx=5, pady=5)

# 실행 프레임
frame_run = Frame(root)
frame_run.pack(fill="x", padx=5, pady=5)

btn_close = Button(frame_run, padx=5, pady=5, text="닫기", width=12, command=root.quit)
btn_close.pack(side="right", padx=5, pady=5)

btn_start = Button(frame_run, padx=5, pady=5, text="시작", width=12, command=start)
btn_start.pack(side="right", padx=5, pady=5)

root.resizable(False, False)
root.mainloop()