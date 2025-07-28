using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

public class CameraManager : MonoBehaviour
{
    List<Camera> cameras;
    GameObject sunLight;
    LensFlareComponentSRP lensFlareSRP;
    int currentCam = 0;

    // Start is called before the first frame update
    void Start()
    {
        sunLight = GameObject.FindGameObjectWithTag("Sun Light");
        lensFlareSRP = sunLight.GetComponent<LensFlareComponentSRP>();

        cameras = GetCameras();
        NextCamera();
    }
    List<Camera> GetCameras()
    {
        List<Camera> cameras = new List<Camera>();
        foreach (Transform child in transform)
        {
            Camera cameraComponent = child.gameObject.GetComponent<Camera>();
            if (cameraComponent != null)
            {
                cameras.Add(cameraComponent);
            }
        }
        return cameras;
    }

    void NextCamera()
    {
        cameras[currentCam].gameObject.SetActive(true);
        for (var i = 0; i < cameras.Count; i++)
        {
            if (i != currentCam)
            {
                cameras[i].gameObject.SetActive(false);
            }
        }
    }

    // Update is called once per frame
    void Update()
    {
        if (Input.GetKeyDown(KeyCode.RightArrow))
        {
            currentCam = (currentCam + 1) % cameras.Count;
            NextCamera();
        }
        else if (Input.GetKeyDown(KeyCode.LeftArrow))
        {
            currentCam = (currentCam - 1 + cameras.Count) % cameras.Count;
            NextCamera();
        }
        // Check if the sun can be seen, if not disable flare.
        EnableFlareSRP();
    }

    void EnableFlareSRP()
    {
        lensFlareSRP.enabled = IsObjectInView(sunLight, cameras[currentCam]);
    }

    public static bool IsObjectInView(GameObject obj, Camera cam)
    {
        // Convert the object's position to viewport space
        Vector3 viewportPoint = cam.WorldToViewportPoint(obj.transform.position);

        // Check if the viewport point is within the camera's view frustum
        bool isInViewport = viewportPoint.x >= -1 && viewportPoint.x <= 1 &&
                            viewportPoint.y >= -1 && viewportPoint.y <= 1 &&
                            viewportPoint.z > -1;

        if (!isInViewport)
            return false;

        // Perform a raycast to check if there's any obstruction
        Ray ray = cam.ScreenPointToRay(cam.WorldToScreenPoint(obj.transform.position));
        RaycastHit hit;

        // Check if the ray hits any object before reaching the target object
        if (Physics.Raycast(ray, out hit))
        {
            if (hit.collider.gameObject != obj)
            {
                return false; // There's something in between
            }
        }

        return true; // Object is visible and not blocked
    }
}