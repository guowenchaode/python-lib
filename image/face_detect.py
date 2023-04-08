# Example 6.1 OpenCV face detection
import cv2
import imutils


def detect_face(image_path, show_image=False):
    img = cv2.imread(image_path)
    img = imutils.resize(img, width=700)

    cascade_classifier = cv2.CascadeClassifier(
        r'D:\Git\github\opencv\data\haarcascades\haarcascade_frontalface_default.xml')

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = cascade_classifier.detectMultiScale(gray, scaleFactor=1.2,
                                                minNeighbors=5,
                                                minSize=(30, 30))
    print(f'there are {len(faces)} faces in {image_path}')

    if show_image:
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x+w, y+h), (255, 255, 0), 2)
            cv2.putText(img, 'face', (x + 10, y + 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)

        cv2.imshow('face', img)
        cv2.waitKey(0)
    return faces


if __name__ == "__main__":
    image_path = r"X:\WD-PHONE\Camera\person-face\IMG_20220617_191109.jpg"
    detect_face(image_path, True)
