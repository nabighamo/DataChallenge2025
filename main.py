import matplotlib.pyplot as plt
import h5py as h5
import numpy as np
import cv2, math
from skimage import morphology,filters, util
from diptest import diptest
import seaborn as sns
import pandas as pd
import os
def analyze(filePath,destinationPath,_callback = None):
    file = h5.File("{}".format(filePath), 'r')
    # testImages = ['Image 0008','Image 0009','Image 0019','Image 0027']
    df_total = pd.DataFrame()
    testImages = file.keys()
    T1 = 7 #We deduced this value experimentally (tested on different data samples).
    for k in testImages:
        imagename = k
        image1 = file[imagename]
        image1 = file[imagename][:image1.shape[1]]

        image_uint8 = util.img_as_ubyte(image1 / np.max(image1))
        footprint = morphology.footprint_rectangle((30, 1))
        filtered = filters.rank.mean_bilateral(image_uint8, footprint, s0=10, s1=10)

        # Step 3: Apply thresholding
        _, thresholded = cv2.threshold(filtered, 125, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C)  # Lower threshold if line is dimmed
        if np.mean(thresholded) > 200:
            thresholded = abs(255 - thresholded)
        window_height = 30
        h, w = thresholded.shape

        # Normalize thresholded image to binary (0 or 1)
        binary = (thresholded > 0).astype(np.uint8)
        binary2 = (thresholded>0)
        num_windows = math.ceil(h / window_height)
        column_window_sums = np.zeros((num_windows, w), dtype=np.uint16)

        for win in range(num_windows):
            start_row = win * window_height
            end_row = start_row + window_height
            window_slice = binary[start_row:end_row, :]
            # window_slice2 = binary[:start_row:end_row]
            column_window_sums[win,:] = window_slice.sum(axis=0)
        column_window_sums[column_window_sums<T1] = 0

        defect_columns = np.where(column_window_sums >= T1)[1]
        affected_windows_per_column = {}
        for col in defect_columns:
            count = np.count_nonzero(column_window_sums[:, col])
            if count == 1 and column_window_sums[:, col].sum() <13:
                column_window_sums[:, col] = 0
            else:
                lbl = int(col)
                affected_windows_per_column[lbl] = count
        if affected_windows_per_column:
            fig,ax=plt.subplots(2,2,figsize=(16, 9))

            ax[0][0].set_title("Original Image")
            ax[0][0].imshow(image_uint8,cmap='gray')
            fig.suptitle("Local Dark Pixel Density {}".format(k))
            ax[0][1].imshow(thresholded,cmap='gray')
            ax[0][1].set_title("Thresholded and smoothed Image")
            # if affected_windows_per_column:
            plt1=ax[1][0].imshow(column_window_sums, cmap='hot', aspect='auto')
            cbar = fig.colorbar(plt1, ax=ax[1][0])
            cbar.set_label("White Spot Count in 30-px Window")
            ax[1][0].set_title("Column HeatMap")
            fig.delaxes(ax[1][1])
            fig.savefig('./results/{}.png'.format(k))
            plt.close()
            data_dict = {}
            for col in affected_windows_per_column.keys():
                data_dict[col] = column_window_sums[:, col]

            # Create DataFrame from dict
            df = pd.DataFrame(data_dict)
            df['window'] = df.index  # Add window index for x-axis

            # Melt for grouped bar chart
            df_melted = df.melt(id_vars='window', var_name='column', value_name='value')
            df_melted['frame'] = k
            df_melted['windows_total'] = num_windows
            df_total = pd.concat([df_total,df_melted])

        # if _callback:
        #     _callback((index+1)/len(testImages)*100)
    print("analysis done!")
    dict_analysis = {"frame":[],'column':[],'windows':[],"values_mean":[],"values_sd":[],"type":[],"start":[],"end":[]}

    #types can be F:fractioned, C:complete,
    if df_total.shape[0]>0:
        df_c = df_total.copy()
        df_c = df_c[df_c['value'] >0]
        frames = list(df_c['frame'].unique())
        for frame in frames:
            df_f = df_c.copy()
            df_f = df_f[df_f['frame'] == frame]
            columns = list(df_f['column'].unique())
            type = ""
            for column in columns:
                df_col = df_f.copy()
                df_col = df_col[df_col['column'] == column]
                nb_windows = df_f.shape[0]
                if nb_windows == 1:
                    min_index = df_col['window'].iloc[0]
                    max_index = min_index
                    type = "Partial"
                else:
                    min_index = df_col['window'].min()
                    max_index = df_col['window'].max()
                    total_windows = df_col['windows_total'].iloc[0]
                    if (max_index - min_index)/total_windows >=0.7:
                        type = 'Complete'
                    else:
                        type = 'Partial'
            dict_analysis['frame'].append(frame)
            dict_analysis['column'].append(column)
            dict_analysis['windows'].append(nb_windows)
            dict_analysis['values_mean'].append(df_col['value'].mean())
            dict_analysis['values_sd'].append(df_col['value'].std())
            dict_analysis['start'].append(min_index)
            dict_analysis['end'].append(max_index)
            dict_analysis['type'].append(type)

        df_analysis = pd.DataFrame(dict_analysis)
        df_analysis['frame'] = df_analysis['frame'].apply(lambda x: int(x.replace("Image ","")))
        df_analysis = df_analysis.sort_values(['column','frame']).reset_index(drop=True)
        def assign_groups(group):
            group = group.copy()
            group["frame_diff"] = group["frame"].diff().fillna(1)
            group["chunk"] = (group["frame_diff"] > 1).cumsum()
            return group

        df_analysis = df_analysis.groupby("column", group_keys=False).apply(assign_groups)

        def label_status(subgroup):
            frames = subgroup["frame"].values
            status = "temporal"
            for i in range(len(frames) - 2):
                if frames[i+1] == frames[i] + 1 and frames[i+2] == frames[i] + 2:
                    status = "constant"
                    break
            subgroup["status"] = status
            return subgroup

        df_analysis = df_analysis.groupby(["column", "chunk"], group_keys=False).apply(label_status)
        df_analysis = df_analysis.drop(columns=["frame_diff"])