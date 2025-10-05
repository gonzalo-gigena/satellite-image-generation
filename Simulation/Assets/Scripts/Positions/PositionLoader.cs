using System.Collections.Generic;
using UnityEngine;
using Newtonsoft.Json;

public class Positions
{
    public string output_folder { get; set; }
    public string mode { get; set; }
    public int total { get; set; }
    public List<double> time_elapsed { get; set; }
    public List<List<double>> subsolar_points { get; set; } // latitude and longitude
    public List<List<double>> sun_pos { get; set; } // x, y, z coordinates
    public List<double> starting_orientation { get; set; } // x, y, z degrees
    public int num_burst { get; set; } // number of rotations per position.
    public int frames { get; set; } // number of rotations per position.
    public List<Satellites> satellites { get; set; }
}

public class Satellites
{
    public string name { get; set; }
    public List<List<double>> pos { get; set; } // x, y , z coordinates
    public List<List<List<double>>> rotations { get; set; } // x, y, z degrees
}

public class PositionLoader
{
    private string jsonFilePath = "generated_positions";

    public Positions LoadData()
    {
        TextAsset jsonFile = Resources.Load<TextAsset>(jsonFilePath);
        string jsonContent = jsonFile.text;
        Positions positions = JsonConvert.DeserializeObject<Positions>(jsonContent);

        return positions;
    }

}