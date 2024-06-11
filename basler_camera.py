from pypylon import pylon
import cv2
import os


class BaslerCamera:
    """
    A class to interact with a Basler camera using pypylon and OpenCV.
    """

    def __init__(self):
        """
        Initializes the BaslerCamera object and opens a connection to the first available camera.
        """
        self.basler_camera = pylon.InstantCamera(
            pylon.TlFactory.GetInstance().CreateFirstDevice()
        )
        self.basler_camera.Open()

    def set_frames_per_second(self, frames_per_second):
        """
        Sets the frame rate for the camera.

        Args:
            frames_per_second (float): The desired frame rate in frames per second.
        """
        self.frames_per_second = frames_per_second
        self.basler_camera.AcquisitionFrameRateEnable.SetValue(True)
        self.basler_camera.AcquisitionFrameRateAbs.SetValue(frames_per_second)

    def set_output_file(self, path, extra_name, base_file_name='basler-camera'):
        """
        Sets the output file for recording the video.

        Args:
            path (str): The directory where the output file will be saved.
            extra_name (str): An additional name to be added to the base file name.
            base_file_name (str, optional): The base name of the output file. Defaults to 'basler-camera'.
        """
        fourcc = cv2.VideoWriter_fourcc(*'MP4V')

        frame_width = int(self.basler_camera.Width.Value)
        frame_height = int(self.basler_camera.Height.Value)

        # Construct the full output file name and path
        self.output_file_name = f"{base_file_name}_{extra_name}.mp4"
        self.output_path = os.path.join(path, self.output_file_name)

        # Create the VideoWriter object for recording
        self.out = cv2.VideoWriter(
            self.output_path, fourcc, self.frame_rate, (frame_width, frame_height)
        )

    def start_recording(self):
        """
        Starts the camera recording.
        """
        self.basler_camera.StartGrabbing()

    def stop_recording(self):
        """
        Stops the camera recording.
        """
        self.basler_camera.StopGrabbing()
        self.Close()

        if self.out is not None:
            self.out.release()

    def capture_frame(self):
        """
        Captures a single frame from the Basler camera, converts it to BGR color format,
        and writes it to the output file.
        """
        try:
            grab_result = self.basler_camera.RetrieveResult(
                5000, pylon.TimeoutHandling_ThrowException
            )
            if grab_result.GrabSucceeded():
                img = grab_result.Array
                img_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                self.out.write(img_bgr)
            grab_result.Release()
        except Exception as e:
            print(f"Error during Basler capture: {e}")