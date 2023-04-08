# Example 6.1 OpenCV face detection
import cv2
import imutils
import face_recognition

def detect_face(image_path):
    img = cv2.imread(image_path)
    img = imutils.resize(img, width=700)

    cascade_classifier = cv2.CascadeClassifier(
        r'D:\Git\github\opencv\data\haarcascades\haarcascade_frontalface_default.xml')

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = cascade_classifier.detectMultiScale(gray, scaleFactor=1.2,
                                                minNeighbors=5,
                                                minSize=(30, 30))

    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x+w, y+h), (255, 255, 0), 2)
        cv2.putText(img, 'face', (x + 10, y + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)

    cv2.imshow('face', img)
    cv2.waitKey(0)


def detect_face_icon(image_path):
    image = cv2.imread(image_path)
    cv2.imshow('photo', image)

    rgb_frame = image[:, :, ::-1]  # Convert to RGB format
    face_locations = face_recognition.face_locations(rgb_frame)

    count = 0
    for face_location in face_locations:
        count = count + 1
        top, right, bottom, left = face_location
        print("Face {} Top: {}, Left: {}, Bottom: {}, Right: {}".format(
            count, top, left, bottom, right))

        face_image = image[top:bottom, left:right]
        title = 'face' + str(count)
        cv2.imshow(title, face_image)

    cv2.waitKey(0)
    cv2.destroyAllWindows()


image_path = r"X:\WD-PHONE\Camera\IMG_20220612_165759.jpg"
detect_face(image_path)
# detect_face_icon(image_path)
