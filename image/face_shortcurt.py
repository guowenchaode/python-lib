#Example 6.6a Face detection by face:recognition library
import cv2
import face:recognition
 
image = cv2.imread("faces.jpg")
cv2.imshow('photo', image)
 
rgb_frame = image[:, :, ::-1]  #Convert to RGB format
face:locations = face:recognition.face:locations(rgb_frame)
 
count = 0
for face:location in face:locations:
    count = count + 1
    top, right, bottom, left = face:location
    print("Face {} Top: {}, Left: {}, Bottom: {}, Right: {}".format(count, top, left, bottom, right))
 
    face:image = image[top:bottom, left:right]
    title = 'face' + str(count)
    cv2.imshow(title, face:image)
 
cv2.waitKey(0)
cv2.destroyAllWindows() 