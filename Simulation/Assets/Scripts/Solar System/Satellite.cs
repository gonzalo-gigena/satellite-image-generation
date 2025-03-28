using UnityEngine;
using System.Collections.Generic;
using System;

public class Satellite : Body
{   
    public List<double> originalPos;
    public string name;
    public double time;

    // Start is called before the first frame update
    public Satellite(GameObject obj)
    {
        body = obj;
    }

    public void LookAt(GameObject obj){
        body.transform.LookAt(obj.transform);
    }

    public void UpdateProperties(double timeElapsed, string satName, List<double> satPosition){
        time = timeElapsed;
        name = satName;
        originalPos = satPosition;
    }
}
