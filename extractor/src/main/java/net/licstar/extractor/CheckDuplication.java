package net.licstar.extractor;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;

/**
 * Created by licstar on 2016/2/3.
 */
public class CheckDuplication {


    public static void main(String[] args) {
        if(args.length != 2){
            System.out.println("usage: java -jar CheckDuplication input_file index_file");
            return;
        }
        try {
            String md5 = FileHash.getMD5(args[0]);
            List<String> result = new ArrayList<String>();

            FileInputStream fis = new FileInputStream(args[1]);
            InputStreamReader isr = new InputStreamReader(fis, "UTF-8");
            Scanner sc=new Scanner(isr);
            while(sc.hasNext()){
                String line = sc.nextLine();
                String[] part = line.split(" ");
                if(part[1].equals(md5)){
                    result.add(part[0]);
                }
            }

            if(result.size() == 0){
                System.out.println("cannot find duplication");
            }else{
                for (String s: result) {
                    System.out.println(s);
                }
            }
        } catch (IOException e) {
            e.printStackTrace();
        }

    }
}
