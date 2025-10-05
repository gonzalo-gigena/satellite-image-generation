using UnityEngine;
using System.IO;
using System.Collections.Generic;
using System.Collections;

public class SatelliteCamera : MonoBehaviour
{
    Satellite sat;
    string ofolder;
    string screenshotFolder;
    public float lookSpeed = 10f;  // Speed of looking around

    private RenderTexture _renderTexture;
    private Texture2D _screenshotTexture;


    public void SetReferences(Satellite satellite, string output_folder)
    {
        sat = satellite;
        ofolder = output_folder;

    }

    // Function to randomize the camera's rotation
    public void SetCameraRotation(List<double> rotation)
    {
        // Get the camera attached to the current GameObject (this script is attached to the camera)
        Camera camera = GetComponent<Camera>();

        // Apply random rotation to the camera
        camera.transform.rotation = Quaternion.Euler((float)rotation[0], (float)rotation[1], (float)rotation[2]);
    }

    void Start()
    {
        int width = 1280;
        int height = 1280;
        _renderTexture = new RenderTexture(width, height, 24);
        _screenshotTexture = new Texture2D(width, height, TextureFormat.RGB24, false);
        screenshotFolder = Path.Combine(Application.dataPath, $"../../SyntheticImages/{ofolder}");
        // Create the screenshot folder if it doesn't exist
        if (!Directory.Exists(screenshotFolder))
        {
            Directory.CreateDirectory(screenshotFolder);
        }
    }

    void LateUpdate()
    {
        GameObject satBody = sat.GetBody();

        if (transform.position != satBody.transform.position)
        {
            transform.position = satBody.transform.position;
        }
        // Camera rotation
        if (Input.GetMouseButton(1)) // Right mouse button
        {
            float mouseX = Input.GetAxis("Mouse X") * lookSpeed;
            float mouseY = Input.GetAxis("Mouse Y") * lookSpeed;

            transform.eulerAngles += new Vector3(-mouseY, mouseX, 0);
        }
        // Check for the screenshot key press
        if (Input.GetKeyDown(KeyCode.Return))
        {
            StartCoroutine(CaptureScreenshot());
        }
    }


    public IEnumerator CaptureScreenshot()
    {
        yield return new WaitForEndOfFrame();

        Camera camera = GetComponent<Camera>();
        camera.targetTexture = _renderTexture;
        camera.Render();

        RenderTexture.active = _renderTexture;
        _screenshotTexture.ReadPixels(new Rect(0, 0, _renderTexture.width, _renderTexture.height), 0, 0);
        _screenshotTexture.Apply();

        byte[] data = _screenshotTexture.EncodeToJPG(93);
        File.WriteAllBytes(GenerateScreenshotPath(), data);

        camera.targetTexture = null;
        RenderTexture.active = null;
    }

    string GenerateScreenshotPath()
    {
        Quaternion quaternion = transform.rotation;
        string satRot = $"{quaternion.x},{quaternion.y},{quaternion.z},{quaternion.w}";
        string satPos = string.Join(",", sat.position);

        string filePath = $"{screenshotFolder}/{sat.name}_{sat.index}_{sat.numBurst}_{sat.burstIndex}_{sat.time}_{satPos}_{satRot}.jpg";

        return filePath;
    }
}
