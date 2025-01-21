# MorphoContour
# A lightweight Python library for precise boundary extraction of droplets, bubbles, cells, and more.
#
# Copyright (c) 2024 A.R. Hashemi
#
# This program is licensed under the European Union Public License (EUPL) v1.2 with additional terms.
# You may not use this software except in compliance with the License.
# You may obtain a copy of the License at:
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12
#
# Additional Terms:
# - The software may not be used for activities violating the United Nations Universal Declaration of Human Rights (UDHR).
# - Commercial use is allowed but requires clear attribution as specified in the repository.
# - Modifications must retain this license and explicitly indicate changes.
#
# For more information, see the LICENSE file in the repository.

import cv2
import numpy as np
import matplotlib.pyplot as plt
import operator # for sorting and comparing
import pyefd

def enhance_contrast(image, clipLimit=2.0, tileGridSize=(8, 8)):
    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=clipLimit, tileGridSize=tileGridSize)
    return clahe.apply(gray)

def crop_and_remove_nozzle(image, x_offset=0, y_offset=0):
    cropped = image[y_offset:, x_offset:]  # Crop the right side of the image
    return cropped

def detect_droplet_boundary(image):
    # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(image, (5, 5), 0)
    edges = cv2.Canny(gray, 50, 200)
    return edges

def process_image(img, threshold=100):   
    # convert to gray
    gray = img#cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # threshold
    thresh = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)[1]

    # morphology edgeout = dilated_mask - mask
    # morphology dilate
    # kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
    # dilate = cv2.morphologyEx(thresh, cv2.MORPH_DILATE, kernel)
    
    # Downsize image (by factor 4) to speed up morphological operations
    # gray = cv2.resize(gray, dsize=(0, 0), fx=0.25, fy=0.25)

    # Morphological Closing: Get rid of the hole
    # gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))

    # Morphological opening: Get rid of the stuff at the top of the circle
    # dilate = cv2.morphologyEx(gray, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (121, 121)))


    # get absolute difference between dilate and thresh
    # diff = cv2.absdiff(dilate, thresh)

    # invert
    # edges = 255 - diff

    # write result to disk
    # cv2.imwrite("process"+"/"+file+"_thresh.jpg", thresh)
    # cv2.imwrite("process"+"/"+file+"_dilate.jpg", dilate)
    # cv2.imwrite("process"+"/"+file+"_diff.jpg", diff)
    # cv2.imwrite("process"+"/"+file+"_edges.jpg", edges)

    # # display it
    # cv2.imshow("thresh", thresh)
    # cv2.imshow("dilate", dilate)
    # cv2.imshow("diff", diff)
    # cv2.imshow("edges", edges)
    # cv2.waitKey(0)
    return thresh#dilate# diff# edges

def measure_nozzle_diameter(edges):
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        image = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        for contour in contours:
            # Get the minimum area rectangle that contains the contour
            rect = cv2.minAreaRect(contour)
    
            # Get the four vertices of the rectangle
            box = cv2.boxPoints(rect)
            box = np.int0(box)
    
            # Draw the rectangle on the original image
            
            cv2.drawContours(image, [box], -1, (255, 0, 0), 2)
            
            # Print the coordinates of the rectangle
            print(f"Rectangle found at {box.flatten().tolist()}")
            
        # cv2.imwrite('droplet_boundary.jpg', image)

def contour_intersect(cnt_ref,cnt_query, edges_only = True):
    
    intersecting_pts = []
    
    ## Loop through all points in the contour
    for pt in cnt_query:
        x,y = pt[0]

        ## find point that intersect the ref contour
        ## edges_only flag check if the intersection to detect is only at the edges of the contour
        
        if edges_only and (cv2.pointPolygonTest(cnt_ref,(x,y),True) == 0):
            intersecting_pts.append(pt[0])
        elif not(edges_only) and (cv2.pointPolygonTest(cnt_ref,(x,y),True) >= 0):
            intersecting_pts.append(pt[0])
            
    if len(intersecting_pts) > 0:
        return True
    else:
        return False
    
def get_centroid(contour):
    M = cv2.moments(contour)
    if M['m00'] != 0:
        cx = int(M['m10']/M['m00'])
        cy = int(M['m01']/M['m00'])        
    else:
        # Handle the case where the contour is a line or a point
        # by taking the first point of the contour
        cx, cy = contour[0][0]
        
    return (cx, cy)

# This function samples points along the line connecting c1 and c2, checks their intensity, and returns the coordinates of the darkest point
def find_darkest_point(img, c1, c2):
    # Create a line iterator for the line between c1 and c2
    line_iterator = cv2.LineIterator(img, c1, c2, 8)
    
    # Initialize variables to store the darkest point and its intensity
    darkest_point = None
    min_intensity = 255  # Assuming 8-bit grayscale image
    
    # Iterate over the points in the line
    for point in line_iterator:
        # Get the intensity of the current point
        intensity = img[point[0][1], point[0][0]]
        
        # Update the darkest point if the current intensity is lower
        if intensity < min_intensity:
            min_intensity = intensity
            darkest_point = (point[0][0], point[0][1])
    
    return darkest_point

# Function for splitting a contour at a given point
def split_contour_at_point(contour, split_point):
    # Find the index of the contour point closest to the split_point
    distances = np.sqrt((contour[:, :, 0] - split_point[0]) ** 2 + (contour[:, :, 1] - split_point[1]) ** 2)
    min_distance_index = np.argmin(distances)
    
    # Split the contour into two parts at the index
    contour_part1 = contour[:min_distance_index]
    contour_part2 = contour[min_distance_index:]
    
    # Return the two new contours
    return contour_part1, contour_part2


# Function to check the gradient change
def check_gradient(image, contour):
    # Find the centroid or a point inside the contour
    M = cv2.moments(contour)
    if M['m00'] != 0:
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
    else:
        # Handle the case where the contour is a line or a point
        # by taking the first point of the contour
        cx, cy = contour[0][0]

    # Define the step size for moving towards the boundary
    step_size = 1

    # Move towards the boundary of the contour
    for i in range(0, len(contour), step_size):
        point = contour[i][0]
        x, y = point

        # Check the color intensity at the current point
        intensity_centroid = image[cy][cx]
        intensity_boundary = image[y][x]

        # Check for gradient change from white to dark
        if intensity_boundary < intensity_centroid:
            # Gradient change detected, accept the contour
            return True

    # No gradient change detected, reject the contour
    return False

def apply_fourier_transform(gray_image):
    # Load the image in grayscale
    # image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # Apply 2D Discrete Fourier Transform (DFT)
    dft = cv2.dft(np.float32(gray_image), flags=cv2.DFT_COMPLEX_OUTPUT)
    dft_shift = np.fft.fftshift(dft)

    # Create a mask with high-pass filter (1s in the corners, 0s in the center)
    rows, cols = gray_image.shape
    crow, ccol = rows // 2, cols // 2
    mask = np.ones((rows, cols, 2), np.uint8)
    r = 10  # Radius of the low frequencies to block
    center = [crow, ccol]
    x, y = np.ogrid[:rows, :cols]
    mask_area = (x - center[0]) ** 2 + (y - center[1]) ** 2 <= r*r
    mask[mask_area] = 0

    # Apply the mask to the shifted DFT
    fshift = dft_shift * mask

    # Inverse DFT to get the image back
    f_ishift = np.fft.ifftshift(fshift)
    img_back = cv2.idft(f_ishift)
    img_back = cv2.magnitude(img_back[:, :, 0], img_back[:, :, 1])

    # Normalize the image for display
    cv2.normalize(img_back, img_back, 0, 255, cv2.NORM_MINMAX)
    img_back = np.uint8(img_back)

    # Display the original and processed images
    # cv2.imshow('Original Image', image)
    # cv2.imshow('Image after High-Pass Filter', img_back)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    # cv2.imwrite("process"+"/"+image_path+'_fourier.jpg', img_back)

    return img_back

# A new function that uses Distance Transform
def split_contour(img_gray, contour, image_path="", index=0):
    # Create a binary image from the contour
    # img = np.zeros((480, 640), dtype=np.uint8) # Adjust the size according to your image
    img = np.zeros_like(img_gray)
    cv2.drawContours(img, [contour], -1, 255, -1)
    
    # Apply Distance Transform to the image
    dist = cv2.distanceTransform(img, cv2.DIST_L2, 3)
    cv2.normalize(dist, dist, 0, 255.0, cv2.NORM_MINMAX)
    dist = dist.astype(np.uint8)
    # cv2.imwrite("process"+"/"+image_path+str(index)+'_distanceTransform.jpg', dist)
    
    # Apply a threshold and a dilation to the distance image
    thresh = cv2.threshold(dist, 50, 255, cv2.THRESH_BINARY)[1] # Adjust the threshold value according to your image
    kernel = np.ones((9, 9), dtype=np.uint8) # Adjust the kernel size according to your image
    dilated = cv2.dilate(thresh, kernel)
    # cv2.imwrite("process"+"/"+image_path+str(index)+'_split_contour.jpg', dilated)
    
    # Find the two contours from the dilated image
    contours, hierarchy = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # if len(contours) != 2:
    #     print("Could not find two ellipses")
    #     return None, None
    
    # # Fit an ellipse to each contour
    # ellipse1 = cv2.fitEllipse(contours[0])
    # ellipse2 = cv2.fitEllipse(contours[1])
    
    # Return the two ellipses
    return contours, hierarchy#ellipse1, ellipse2

def contour_child_finder(contour_index, hierarchy):
    number_of_child = 0
    child_indexes = []
    child_index = hierarchy[0, contour_index, 2]
    while (child_index != -1):
        number_of_child += 1
        child_indexes.append(child_index)
        child_index = hierarchy[0, child_index, 0]        
        
    
    # Find the index of the current contour in the hierarchy
    # index = np.where(hierarchy[0, :, 2] == -1)[0][0]

    # Check if the current contour has a single child
    return number_of_child, child_indexes #hierarchy[0, index, 2] != -1


def measure_droplet_properties(edges, image_path="", save_contour=False):
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # print(hierarchy)

    if contours:        
        # Assuming the largest contour corresponds to the droplet
        # largest_contour = max(contours, key=cv2.contourArea)
        # Calculate area of the droplet
        # area = cv2.contourArea(largest_contour)

        # # Fit an ellipse to the contour to get semi-axes
        # ellipse = cv2.fitEllipse(largest_contour)
        # print(ellipse)
        # print(type(ellipse[0][0]))
        # # major_axis, minor_axis = ellipse[1]

        # return largest_contour, area, ellipse# major_axis, minor_axis,
        ellipses = []
        n = 0
        # i = 0
        for i, contour in enumerate(contours): #while i < len(contours):
            # contour = contours[i]
            number_of_child, child_indexes = contour_child_finder(i, hierarchy)
            # print(f'Number of children for contour {i}: {number_of_child}')
            if number_of_child>1:
                cnts, hiers = split_contour(edges, contour, image_path, i)
                for cnt in cnts:
                    n+=1
                    if len(cnt) >= 5:
                        # Calculate area of the contour
                        area = cv2.contourArea(cnt)
                        perimeter = cv2.arcLength(cnt, False)
                        # print(contour)

                        # Fit an ellipse to the contour to get semi-axes
                        ellipse = cv2.fitEllipseDirect(cnt)
                        if ellipse is not None:

                            major_axis, minor_axis = ellipse[1]
                        # print(f'Major Axis: {major_axis}, Minor Axis: {minor_axis}, Angle: {ellipse[2]}')
                            area_ellipse = np.pi * (major_axis/2) * (minor_axis/2)
                            perimeter_ellipse = 2.0 * np.pi * np.sqrt(((major_axis/2)**2 + (minor_axis/2)**2)/2.0)
                            if area_ellipse > 0 and area > 0:
                                area_ratio = area_ellipse/area
                                perimeter_ratio = perimeter_ellipse/perimeter
                            # print(area_ratio, perimeter_ratio)
                                if np.abs(area_ratio-1) < 0.2 or np.abs(perimeter_ratio-1) < 0.2:#
                                    ellipses.append(ellipse)
                # print(f"Contour {i} has more than one child")
            elif number_of_child==1:
                # print(f"Contour {i} has a single child")
                n+=1
                if len(contour) >= 5:
                    # Calculate area of the contour
                    area = cv2.contourArea(contour)
                    perimeter = cv2.arcLength(contour, False)
                    # print(contour)

                    # Fit an ellipse to the contour to get semi-axes
                    ellipse = cv2.fitEllipseDirect(contour)
                    if ellipse is not None:

                        major_axis, minor_axis = ellipse[1]
                    # print(f'Major Axis: {major_axis}, Minor Axis: {minor_axis}, Angle: {ellipse[2]}')
                        area_ellipse = np.pi * (major_axis/2) * (minor_axis/2)
                        perimeter_ellipse = 2.0 * np.pi * np.sqrt(((major_axis/2)**2 + (minor_axis/2)**2)/2.0)
                        if area_ellipse > 0 and area > 0:
                            area_ratio = area_ellipse/area
                            perimeter_ratio = perimeter_ellipse/perimeter
                            # print(area_ratio, perimeter_ratio)
                            if np.abs(area_ratio-1) < 0.2 or np.abs(perimeter_ratio-1) < 0.2:#
                                ellipses.append(ellipse)
            

        return contours, hierarchy, ellipses, n# major_axis, minor_axis,

        
    else:
        return None, 0, None, 0
    
def draw_contours_with_different_colors(img, contours):
    # Draw each contour with a different color
    color_list = [(0,255,0), (255,0,0), (0,0,255), (255,255,0), (0,255,255), (255,0,255)]
    for i, contour in enumerate(contours):
        color = color_list[i]#tuple(np.random.randint(0, 255, 3).tolist())
        cv2.drawContours(img, [contour], -1, color, 2)

    # Return the image with the contours
    return img

def ellipses_analysis(ellipses, save_ellipse=False, filename_vars=None):
    
    ellipses_sorted = ellipses
    n = 0
    properties = [(0,0,0,0,0)]
    if ellipses:
        # Define a lambda function that returns the area of an ellipse
        area = lambda e: e[1][0] * e[1][1]
        # Sort the list of ellipses by area in descending order
        ellipses_sorted = sorted(ellipses, key=area, reverse=True)        
        n = len(ellipses)
        properties = []
        for ellipse in ellipses_sorted:
            center_x, center_y = ellipse[0]
            major_axis, minor_axis = ellipse[1]
            angle = ellipse[2]
            properties.append((center_x, center_y, major_axis, minor_axis, angle))
        return n, properties, ellipses_sorted
    # else:
    #     n = 0
    #     properties = [(0,0,0)]
    return n, properties, ellipses_sorted

def calculate_pixel_sum(image):
    s1 = np.sum(image, axis=0)
    s2 = np.sum(image, axis=1)
    return s1, s2

def calculate_pixel_grad(s1, s2):
    grad_x = np.gradient(s1)
    grad_y = np.gradient(s2)
    return grad_x, grad_y    

def contour_finder(image_path, crop_x_lim=(400,1100), crop_y_lim=(230,1660), clipLimit=2.0, tileGridSize=(8, 8), threshold=50, binarization_max_val=255, save_contour=False, save_contrast=False, save_binarized=False):
    # Load the image
    # image = cv2.imread(image_path)
    # Crop and remove nozzle
    # x_offset = 220#580
    # y_offset = 0#485
    # cropped_image = crop_and_remove_nozzle(image.copy(), x_offset, y_offset)
    cropped_image = cv2.imread(image_path)[crop_x_lim[0]:crop_x_lim[1], crop_y_lim[0]:crop_y_lim[1]]#, cv2.IMREAD_GRAYSCALE
    # Enhance contrast
    # image_contrast = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    image_contrast = enhance_contrast(cropped_image, clipLimit, tileGridSize)
    if save_contrast:
        cv2.imwrite(image_path+'_contrast.png', image_contrast)
    
    # threshold
    thresh = cv2.threshold(src=image_contrast, thresh=threshold, maxval=binarization_max_val, type=cv2.THRESH_BINARY)[1]
    if save_binarized:
        cv2.imwrite(image_path+'_binarized.png', thresh)
    
    # find contours
    cntrs, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)#cv2.RETR_EXTERNAL
    # cntrs_sorted = sorted(cntrs, key=cv2.contourArea, reverse=True)
    # contours = []
    # contours_area = []
    # contour_centroids = []
    contours_zip = []
    # For each contour, find the bounding rectangle and draw it
    if hierarchy is not None:
        for component in zip(cntrs, hierarchy[0]):
            currentContour = component[0]
            currentHierarchy = component[1]
            if cv2.contourArea(currentContour) < 30000:
                (x,y) = get_centroid(currentContour)
                if y > 20:#100 and y < 1400:# or x < 100 or x > 1000
                    if currentHierarchy[2] != -1:
                        # contours.append(currentContour)
                        # contours_area.append(cv2.contourArea(currentContour))
                        # contour_centroids.append((x,y))
                        contours_zip.append((currentContour, cv2.contourArea(currentContour), (x,y)))
    # for cont in cntrs:#_sorted:
    #     if cv2.contourArea(cont) < 30000:
    #         (x,y) = get_centroid(cont)
    #         if y > 20:#100 and y < 1400:# or x < 100 or x > 1000
                
    #             contours.append(cont)
    #             contours_area.append(cv2.contourArea(cont))
    #             contour_centroids.append((x,y))
    contours_sorted = sorted(contours_zip, key=lambda x: cv2.contourArea(x[0]), reverse=True)
    contours = [x[0] for x in contours_sorted]
    contours_area = [x[1] for x in contours_sorted]
    contour_centroids = [x[2] for x in contours_sorted]
    if save_contour:
        image_with_contours = cropped_image.copy()
        draw_contours_with_different_colors(image_with_contours, contours)
        cv2.imwrite(image_path+'_contours.jpg', image_with_contours)
    # image_with_contours = cropped_image.copy()
    # draw_contours_with_different_colors(image_with_contours, contours)
    # cv2.imwrite(image_path+'_contours.jpg', image_with_contours)
    
    return contours, contours_area, contour_centroids, hierarchy

def contour_fourier_features(contour, order=10):
    coeffs = pyefd.elliptic_fourier_descriptors(contour, order=order)
    a0, c0 = pyefd.calculate_dc_coefficients(contour)
    return coeffs, a0, c0

def gradient_labeling(image_path):
    # Load the image
    image = cv2.imread(image_path)
    # Crop and remove nozzle
    x_offset = 220#580
    y_offset = 0#485
    cropped_image = crop_and_remove_nozzle(image.copy(), x_offset, y_offset)
    
    # Enhance contrast
    image_contrast = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)#enhance_contrast(cropped_image)#cv2.GaussianBlur(image, (5, 5), 0)#
    
    # Detect droplet boundary
    # edges = detect_droplet_boundary(image_contrast)
    # edges = process_image(image_contrast)
    
    # threshold
    thresh = cv2.threshold(image_contrast, 50, 255, cv2.THRESH_BINARY)[1]
    
    fig1 = plt.figure()
    plt.imshow(thresh, cmap='gray')
    fig1.savefig(image_path+'edges.png', dpi=300)
    
    sx, sy = calculate_pixel_sum(thresh)
    grad_x, grad_y = calculate_pixel_grad(sx, sy)
    
    sx = sx/np.max(sx)
    sy = sy/np.max(sy)
    grad_x = grad_x/np.max(grad_x)
    grad_y = grad_y/np.max(grad_y)
        
    # Create a figure with 3 subplots
    fig, axs = plt.subplots(nrows=1, ncols=3, figsize=(12, 4))

    # Plot the image on the first subplot
    axs[0].imshow(cropped_image, cmap='gray')
    axs[0].set_title('Image')
    
    axs[1].plot(sx, label='Sum')
    axs[1].plot(grad_x, label='Gradient')
    axs[1].set_title('Sum and gradient along x axis')
    axs[1].legend()
    
    axs[2].plot(sy, label='Sum')
    axs[2].plot(grad_y, label='Gradient')
    axs[2].set_title('Sum and gradient along y axis')
    axs[2].legend()
    
    # Adjust the spacing between subplots
    fig.tight_layout()
    
    fig.savefig(image_path+'_morphology.jpg', dpi=300)
    # Show the figure
    # plt.show()

    return grad_x, grad_y, sx, sy

def droplet_volume_estimation(img_path):
    # Load the image
    image = cv2.imread(img_path)

    # Crop and remove nozzle
    # x_offset = 220
    # y_offset = 0
    # cropped_image = crop_and_remove_nozzle(image.copy(), x_offset, y_offset)
    img = image.copy()[550:1000, 251:1000]
    img = cv2.transpose(img)
    
    # Enhance contrast
    image_contrast = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    
    # image_contrast = cv2.GaussianBlur(image_contrast, (5, 5), 0)
    
    image_contrast = process_image(image_contrast,50)
    
    # cv2.imwrite(img_path + '_processed.jpg', image_contrast)
    # Set the threshold for intensity change to detect the droplet boundary
    intensity_threshold = 0  # Since the image was binarized

    # Initialize the total volume
    total_volume = [0.0]
    num_droplets = 0
    x_diameter_max = 0.0
    y_diameter_max = 0.0
    x_diameters = [0.0]
    y_diameters = []
    y_white = []
    
    pixel2um = 70.0/160.0 # Assuming 70 um per 160 pixels
    
    # image_c = img.copy()
    
    # Iterate over each row in the image
    for y in reversed(range(image_contrast.shape[0])):
        row = image_contrast[y, :]
        # Find indices where the intensity changes suddenly
        change_indices = np.where((np.abs(np.diff(row))) > intensity_threshold)[0]
        
        if len(change_indices) == 2:
            diameter = (change_indices[1] - change_indices[0])*pixel2um
            # Calculate the radius (in pixels)
            radius = diameter / 2.0
            # Calculate the volume of the cylinder (πr²h, with h=1 pixel)
            volume_cylinder = np.pi * (radius ** 2) * pixel2um
            if x_diameters[-1] < diameter:
                x_diameters[-1] = diameter
            # Add the volume of the cylinder to the total volume
            total_volume[-1] += volume_cylinder
            # cv2.circle(image_c, (int(change_indices[0]), y), int(0), (0, 0, 255), thickness=-1)
            # cv2.circle(image_c, (int(change_indices[1]), y), int(0), (0, 255, 0), thickness=-1)
        elif len(change_indices) > 2:
            diameter = (change_indices[-1] - change_indices[0])*pixel2um
            radius = diameter / 2.0
            volume_cylinder = np.pi * (radius ** 2) * pixel2um
            total_volume[-1] += volume_cylinder
            if x_diameters[-1] < diameter:
                x_diameters[-1] = diameter
            # cv2.circle(image_c, (int(change_indices[0]), y), int(0), (0, 0, 255), thickness=-1)
            # cv2.circle(image_c, (int(change_indices[-1]), y), int(0), (0, 255, 0), thickness=-1)
        elif len(change_indices) < 2:
            num_droplets += 1
            total_volume.append(0.0)
            x_diameters.append(0.0)
            y_white.append(y)
            # cv2.circle(image_c, (int(0), y), int(0), (255, 0, 0), thickness=-1)
    if len(y_white) > 0:
        for i in range(len(y_white)-1):
            if np.abs(y_white[i+1] - y_white[i]) > 1:
                y_diameters.append((y_white[i+1] - y_white[i])*pixel2um)
                
        # y_diameter_max = np.max(np.array(y_diameters))#*pixel2um
    # cv2.imwrite(img_path + '_indices.jpg', image_c)
    x_diameters = [i for i in x_diameters if i != 0]
    y_diameters = [i for i in y_diameters if i != 0]
    total_volume = [i for i in total_volume if i != 0]
    num_droplets = len(total_volume)
    return  total_volume, num_droplets, x_diameters, y_diameters

    

def droplet_boundary(image_path, save_ellipse=False, save_contour=False):

    # Load the image
    image = cv2.imread(image_path)
    
    
    # edges = process_image(image)
    # cv2.imwrite("process"+"/"+image_path+'_morphology.jpg', edges)
    # # convert to gray
    # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # ft_image = apply_fourier_transform(gray)
    # # # threshold
    # thresh =  ft_image#cv2.adaptiveThreshold(ft_image,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,11,2)#cv2.threshold(ft_image, 2, 255, cv2.THRESH_BINARY)[1]
    # thresh = process_image(ft_image)
    
    # Crop and remove nozzle
    x_offset = 220#580
    y_offset = 0#485
    cropped_image = crop_and_remove_nozzle(image.copy(), x_offset, y_offset)
    
    # Enhance contrast
    image_contrast = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)#enhance_contrast(cropped_image)#cv2.GaussianBlur(image, (5, 5), 0)#

    
    
    # Detect droplet boundary
    # edges = detect_droplet_boundary(image_contrast)
    edges = process_image(image_contrast)
    
    # measure_nozzle_diameter(edges)

    # Measure droplet properties  largest_contour, area, 
    contours, hierarchy, ellipses, n = measure_droplet_properties(edges, image_path)
    
    ellipses_with_offset = []
    # Draw fitted ellipse on the original image
    if ellipses:
        # image_with_ellipse = cropped_image.copy()        
        for ellipse in ellipses:
            _ellipse = list(ellipse)
            _centre = list(_ellipse[0])
            _centre[0] = _centre[0] + x_offset # add x offset to draw ellipse in original image coordinates
            _centre[1] = _centre[1] + y_offset # add x offset to draw ellipse in original image coordinates
            _ellipse[0] = tuple(_centre) # update ellipse centre
            ellipse = tuple(_ellipse)
            ellipses_with_offset.append(ellipse)
        # cv2.ellipse(image_with_ellipse, ellipse, (0, 255, 0), 2)
        # print(f'Major Axis: {ellipse[1][1]}, Minor Axis: {ellipse[1][0]}, Angle: {ellipse[2]}')


    # Save the output figures
    # cv2.imwrite(image_path+'enhanced_contrast.jpg', image_contrast)
    # cv2.imwrite("process"+"/"+image_path+'_thresh.jpg', thresh)
    # cv2.imwrite("process"+"/"+image_path+'_Canny.jpg', edges)
    # cv2.imwrite("process"+"/"+image_path+'_ellipses.jpg', image_with_ellipse)
    # image_with_contours = cropped_image.copy()
    # cv2.drawContours(image_with_contours, contours, -1, (255, 0, 0), 2)
    # draw_contours_with_different_colors(image_with_contours, contours)
    # cv2.imwrite("process"+"/"+image_path+'_contours.jpg', image_with_contours)

    # # Set up the detector with default parameters.
    # detector = cv2.SimpleBlobDetector()    
    # # Detect blobs.
    # keypoints = detector.detect(image)    
    # # Draw detected blobs as red circles.
    # # cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS ensures the size of the circle corresponds to the size of blob
    # im_with_keypoints = cv2.drawKeypoints(image, keypoints, np.array([]), (0,0,255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    # cv2.imwrite("process"+"/"+image_path+'_keypoints.jpg', im_with_keypoints)
    

    # Display the results
    # cv2.imshow('Original Image', image)
    # cv2.imshow('Enhanced Contrast', image_contrast)
    # cv2.imshow('Cropped Image', cropped_image)
    # cv2.imshow('Droplet Boundary', edges)
    # cv2.imshow('Droplet with Ellipse', image_with_ellipse)

    # print(f'Droplet Area: {area}')

    

    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    
    return ellipses_with_offset, n

# droplet_boundary('sattlite.jpg')#Captura0.PNG
