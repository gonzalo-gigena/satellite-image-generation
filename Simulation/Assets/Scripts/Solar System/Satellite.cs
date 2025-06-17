using UnityEngine;
using System.Collections.Generic;
using System;

public class Satellite : Body
{   
    public List<double> position;
    public string name;
    public double time;
    public int index, numBurst, burstIndex;

    // Start is called before the first frame update
    public Satellite(GameObject obj)
    {
        body = obj;
    }

    public void LookAt(GameObject obj){
        body.transform.LookAt(obj.transform);
    }

    public void UpdateProperties(double timeElapsed, string satName, List<double> satPosition, int index, int numBurst, int burstIndex)
    {
        this.time = timeElapsed;
        this.name = satName;
        this.position = satPosition;
        this.index = index;
        this.numBurst = numBurst;
        this.burstIndex = burstIndex;
    }
}
