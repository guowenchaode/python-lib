# Example 6.6a Face detection by face_recognition library
import cv2
import face_recognition

image = cv2.imread("faces.jpg")
cv2.imshow("photo", image)

rgb_frame = image[:, :, ::-1]  # Convert to RGB format
face_locations = face_recognition.face_locations(rgb_frame)

count = 0
for face_location in face_locations:
    count = count + 1
    top, right, bottom, left = face_location
    print(
        "Face {} Top: {}, Left: {}, Bottom: {}, Right: {}".format(
            count, top, left, bottom, right
        )
    )

    face_image = image[top:bottom, left:right]
    title = "face" + str(count)
    cv2.imshow(title, face_image)

cv2.waitKey(0)
cv2.destroyAllWindows()
