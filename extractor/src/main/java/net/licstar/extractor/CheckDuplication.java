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

    /**
     * 编辑距离
     *
     * @param a
     * @param b
     * @return
     */
    private static int distance(List<String> a, List<String> b) {
        int dist[][] = new int[a.size() + 1][b.size() + 1];
        for (int i = 0; i < a.size(); i++) {
            for (int j = 0; j < b.size(); j++) {
                int v = 5000;
                if (i == 0 && j == 0) {
                    v = 0;
                } else if (i > 0) {
                    v = Math.min(v, dist[i - 1][j]);
                } else if (j > 0) {
                    v = Math.min(v, dist[i][j - 1]);
                }

                if (a.get(i).equals(b.get(j))) {
                    dist[i][j] = v;
                } else {
                    dist[i][j] = v + 1;
                }
            }
        }
        return dist[a.size() - 1][b.size() - 1];
    }

    /**
     * 相似度
     *
     * @param a
     * @param b
     * @return
     */
    private static double similarity(ArrayList<String> a, ArrayList<String> b) {
        if (a.size() < b.size()) {
            return similarity(b, a);
        }
        if (a.size() > b.size() * 1.5) {
            return 0;
        }
        int dist = 0;
        int size = a.size();
        if (b.size() > 2000) {
            size = 2000;
            dist = distance(a.subList(0, 2000), b.subList(0, 2000));
        } else {
            dist = distance(a, b);
        }
        return 1 - 1.0 * dist / size;
    }

    public static void main(String[] args) {
        if (args.length != 2) {
            System.out.println("usage: java -jar CheckDuplication input_file index_file");
            return;
        }
        try {
            String md5 = FileHash.getSimHash(args[0]);
            List<String> result = new ArrayList<String>();

            FileInputStream fis = new FileInputStream(args[1]);
            InputStreamReader isr = new InputStreamReader(fis, "UTF-8");
            Scanner sc = new Scanner(isr);
            while (sc.hasNext()) {
                String line = sc.nextLine();
                String[] part = line.split(" ");
                if (part[1].equals(md5)) {
                    result.add(part[0]);
                }
            }

            if (result.size() == 0) {
                System.out.println("cannot find duplication");
            } else {
                ArrayList<String> a = FileHash.getSegWordsFromFile(args[0]);
                for (String s : result) {
                    ArrayList<String> b = FileHash.getSegWordsFromFile("/root/testdata2/all/" + s);
                    System.out.println(s + " " + distance(a, b));
                }
            }
        } catch (IOException e) {
            e.printStackTrace();
        }

    }
}
