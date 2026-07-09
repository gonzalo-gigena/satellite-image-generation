using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class UpdatePosition : MonoBehaviour
{
    Sun sun;
    Satellite sat;
    Earth earth;
    Positions positions;
    SatelliteCamera satelliteCameraScript;
    int satellite_index = 0; // for now there is only one satellite
    int i, j, k = 0;

    void Start()
    {
        // Load Postions
        PositionLoader loader = new();
        positions = loader.LoadData();

        // Search objects by tag
        GameObject cubesatObj = GameObject.FindGameObjectWithTag("Cubesat");
        GameObject earthObj = GameObject.FindGameObjectWithTag("Earth");
        GameObject sunObj = GameObject.FindGameObjectWithTag("Sun");

        earth = new Earth(earthObj, Units.EARTH_RADIUS);
        sun = new Sun(sunObj, Units.SUN_RADIUS);
        sat = new Satellite(cubesatObj);

        // Pass reference to satellite camera
        GameObject satelliteCamera = GameObject.Find("SatelliteCamera");
        satelliteCameraScript = satelliteCamera.GetComponent<SatelliteCamera>();
        string ofolder = positions.output_folder;
        string mode = positions.mode;
        satelliteCameraScript.SetReferences(sat, ofolder, mode.Equals("debug"));

        if (mode.Equals("debug"))
        {
            NextPosition();
        }
        else if (mode.Equals("generate"))
        {
            StartCoroutine(CaptureScreenshotsContinuously());
        }
    }

    // Coroutine to capture screenshots continuously
    IEnumerator CaptureScreenshotsContinuously()
    {
        for (int i = 0; i < positions.total; i++)
        {
            // Move to the next position of the planets
            SetPositions(i);
            for (int j = 0; j < positions.num_burst; j++)
            {
                for (int k = 0; k < positions.frames; k++)
                {
                    SetRotation(i, j, k);
                    UpdateSatProperties(i, j, k);

                    // Take a screenshot (wait for end of frame to ensure proper rendering)
                    yield return StartCoroutine(satelliteCameraScript.CaptureScreenshot());

                    // Optionally, yield return null to capture the next frame immediately
                    yield return null;
                }
            }
        }

        StopGame();
    }


    void StopGame()
    {
    #if UNITY_EDITOR
        UnityEditor.EditorApplication.isPlaying = false; // stops play mode in Editor
    #else
        Application.Quit(); // quits the built game
    #endif
    }

    void Update()
    {
        // Manual position stepping is debug-only: in generate mode it would
        // move the scene mid-capture and corrupt the scripted sequence.
        if (!positions.mode.Equals("debug"))
        {
            return;
        }

        // Check if the spacebar is pressed
        if (Input.GetKeyDown(KeyCode.Space))
        {
            // All list inside the Positions object have the same length
            i = (i + 1) % positions.total;
            NextPosition();
        }
    }

    void NextPosition()
    {
        // goes to the next position not photo.
        SetPositions(i);
        SetRotation(i, j, k);
        UpdateSatProperties(i, j, k);
    }

    void UpdateSatProperties(int index, int burstIndex, int frameIndex)
    {
        double timeElapsed = positions.time_elapsed[index] + frameIndex;
        string name = positions.satellites[satellite_index].name;
        List<double> satPosition = positions.satellites[satellite_index].pos[index];
        sat.UpdateProperties(timeElapsed, name, satPosition, index, burstIndex, frameIndex);
    }

    void SetPositions(int index)
    {
        List<double> subsolarPoint = positions.subsolar_points[index];
        List<double> sunPosition = positions.sun_pos[index];
        List<double> satPosition = positions.satellites[satellite_index].pos[index];

        sun.SetPosition(sunPosition);
        earth.SetRotation(subsolarPoint, sun.GetBody());

        sat.SetPosition(satPosition);
        //sat.LookAt(sun.GetBody());
    }

    void SetRotation(int index, int burstIndex, int frameIndex)
    {
        int rotationIndex = burstIndex * positions.frames + frameIndex;
        List<double> rotation = positions.satellites[satellite_index].rotations[index][rotationIndex];
        satelliteCameraScript.SetCameraRotation(rotation);
    }
}