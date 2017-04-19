package com.example.tingyao.smartparkdemo;

import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.Uri;
import android.os.StrictMode;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.TextView;

import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.util.HashMap;

public class MainActivity extends AppCompatActivity implements SensorEventListener{

    //----http connection to parking management server
    MyHttpConnect conn;

    //----destination info: lat and lng
    double deslat;
    double deslng;
    String camid;
    String sid;
    int rowid;

    int controlState;

    //---- GUI
    ImageView imageView;
    Button requestButton;
    TextView textView;

    //---- accelerator sensor (for demo)
    SensorManager smng;

    //---- my navigation
    double lat;
    double lng;
    TTSController ttsobj;
    GPSTracker gpsTracker;

    //demo navigation
    double[] checklats;
    double[] checklngs;
    String[] utts;
    String[] lastutts;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        //---- GUIs
        imageView = (ImageView) findViewById(R.id.imageView);
        requestButton = (Button) findViewById(R.id.request_button);
        textView = (TextView) findViewById(R.id.textView);

        //allow main thread execute network operation
        if (android.os.Build.VERSION.SDK_INT > 9) {
            StrictMode.ThreadPolicy policy = new StrictMode.ThreadPolicy.Builder().permitAll().build();
            StrictMode.setThreadPolicy(policy);
        }
        conn = new MyHttpConnect("http://vid-gpu6.inf.cs.cmu.edu:9001");
        controlState = 0;

        //---- for navigation
        ttsobj = new TTSController(getApplicationContext());
        gpsTracker = new GPSTracker(this);

    }



    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy)
    {
        // TODO Auto-generated method stub
    }
    @Override
    public void onSensorChanged(SensorEvent event)
    {

    }

    public void openGMAP(){
        //String format = "geo:0,0?q=" + lat + "," + lng + "( Location title)";
        String format = "google.navigation:q=" + lat + "," + lng+":mode=walking";

        Uri uri = Uri.parse(format);

        Intent intent = new Intent(Intent.ACTION_VIEW, uri);
        intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
        startActivity(intent);
    }

    public void requestSlot(){
        boolean emptySlot = false;
        //---- preparing parameters for http post
        HashMap<String, String> keyValuePairs = new HashMap<String,String>();
        keyValuePairs.put("cmd", "request_slot");
        String params = conn.SetParams(keyValuePairs);

        //---- post to server and get response
        String rstr="";
        try{
            HttpURLConnection response = (HttpURLConnection)conn.PostToServer(params);
            System.out.println("connection success!");
            int responseCode = response.getResponseCode();
            if(responseCode == HttpURLConnection.HTTP_OK){
                String line;
                BufferedReader br=new BufferedReader(new InputStreamReader(response.getInputStream()));
                while ((line=br.readLine()) != null) {
                    rstr+=line;
                }

            }
        } catch (IOException e){
            System.out.println(e.toString());
            Log.e("NLU", "connection error");
        }
        System.out.println("from server: " + rstr);

        //---- analyze response
        try{
            JSONObject jobj = new JSONObject(rstr);
            emptySlot = jobj.getBoolean("slot");
            if (emptySlot) {
                deslat = jobj.getDouble("lat");
                deslng = jobj.getDouble("lng");
                camid = jobj.getString("camid");
                sid = jobj.getString("slotid");
                rowid = jobj.getInt("rowid");
            }
        } catch (JSONException jsone) {

        }

        //---- get image
        if (emptySlot){
            HashMap<String, String> keyValuePairs2 = new HashMap<String,String>();
            keyValuePairs2.put("cmd", "request_img");
            keyValuePairs2.put("camid", camid);
            keyValuePairs2.put("slotid", sid);
            String params2 = conn.SetParams(keyValuePairs2);

            try{
                HttpURLConnection response = (HttpURLConnection)conn.PostToServer(params2);
                System.out.println("connection success 2!");
                int responseCode = response.getResponseCode();
                if(responseCode == HttpURLConnection.HTTP_OK){

                    BitmapFactory.Options bmOptions;
                    bmOptions = new BitmapFactory.Options();
                    bmOptions.inSampleSize = 1;
                    bmOptions.inJustDecodeBounds = true;

                    InputStream inputStream = response.getInputStream();
                    //Bitmap bitmap = BitmapFactory.decodeStream(response.getInputStream(), null, bmOptions);
                    Bitmap bitmap = BitmapFactory.decodeStream(inputStream);
                    imageView.setImageBitmap(bitmap);

                    textView.setText("An empty slot found! \nPress \"CONFIRM\" or \"CANCEL\"");
                    requestButton.setText("Confirm");
                    controlState = 1;
                }
            } catch (IOException e){
                Log.e("Image Request", "connection error");
            }
        }
    }

    public void confirmSlot(){
        //openGMAP();
        myNavigate();
        controlState = 2;
    }

    public void requestButtonFunc(View v){
        if (controlState==0)
            requestSlot();
        else if(controlState==1)
            confirmSlot();
    }
    public void cancelSlot(View v){
        controlState = 0;
        requestButton.setText("Request");
        imageView.setImageResource(android.R.color.transparent);
        textView.setText("Press \"REQUEST\" to get a parking slot");
    }
    public void test(View v){
        //gpsTracker.getLocation();
        //String testStr = "test latlng: "+gpsTracker.getLatitude()+", "+gpsTracker.getLongitude();
        //textView.setText(testStr);

        lat = 40.494398;
        lng = -80.261303;
        openGMAP();
    }

    /**
     * navigation output utterance (produce both text and speech output)
     * @param s
     */
    public void navigateUtt(String s){
        ttsobj.speakThis(s);
        textView.setText(s);
    }

    public void initialDemoNavigation(){
        utts = new String[3];
        utts[0] = "Turn right";
        utts[1] = "Turn left";
        utts[2] = "go straight";
        lastutts = new String[3];
        lastutts[0] = "Turn left, and the empty spot will be on your left";
        lastutts[1] = "Turn left, and the empty spot will be on your right";
        lastutts[2] = "Turn left, and the empty spot will be on your left";
        checklats = new double[3];
        checklngs = new double[3];
        checklats[0] = 40.495318;
        checklngs[0] = -80.259734;
        checklats[1] = 40.494351;
        checklngs[1] = -80.259763;

        //it could be row id dependent
        checklats[2] = 40.494385;
        checklngs[2] = -80.261022;

    }

    public void myNavigate(){
        Thread t = new Thread(new Runnable() {
            @Override
            public void run() {
                initialDemoNavigation();
                double checklat = checklats[0];
                double checklng = checklats[0];
                int progress = 0;
                while(controlState!=0){
                    lat = gpsTracker.getLatitude();
                    lng = gpsTracker.getLongitude();

                    if (mdis(lat,lng,checklat,checklng)<0.0001){
                        demoNavigator(progress);
                        if (progress==2) break;
                    }
                }
            }
        });
        t.start();
    }

    public void demoNavigator(int progress){
        if(progress==0) navigateUtt("Go straight");
        else if(progress==1) navigateUtt("Turn right");
        else if(progress==2) navigateUtt(lastutts[rowid-1]);
        //else if(progress==3) navigateUtt(lastutts[rowid-1]);
    }

    public double mdis(double x1, double y1, double x2, double y2){
        return Math.abs(x1-x2)+Math.abs(y1-y2);
    }
}
