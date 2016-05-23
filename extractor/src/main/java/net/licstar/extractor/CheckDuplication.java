package net.licstar.extractor;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.*;

/**
 * Created by licstar on 2016/2/3.
 */
public class CheckDuplication {
    static final int WordCountLimit = 2000; //字数限制，大于2000词的文档，只看前2000词。

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
                int v = WordCountLimit + 1;
                if (i == 0 && j == 0) {
                    v = 0;
                }
                if (i > 0) {
                    v = Math.min(v, dist[i - 1][j]);
                }
                if (j > 0) {
                    v = Math.min(v, dist[i][j - 1]);
                }
                if (i > 0 && j > 0) {
                    v = Math.min(v, dist[i - 1][j - 1]);
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
    private static String similarity(List<String> a, List<String> b) {
        if (a.size() < b.size()) {
            return similarity(b, a);
        }
        //可能会有半篇文章相似，因此去掉这个文章长度比较的逻辑
        String suffix = "";
        if (a.size() > b.size() * 1.5) {
            suffix = "-part";
        }

        if (a.size() > WordCountLimit)
            a = a.subList(0, WordCountLimit);
        if (b.size() > WordCountLimit)
            b = b.subList(0, WordCountLimit);

        int dist = distance(a, b);
        int same = a.size() - dist;


        Double ret = 1.0 * same / b.size();
        return ret.toString() + suffix;
    }

    private static double hashSimilarity(String a, String b) {
        int total = a.length();
        int same = 0;
        for (int i = 0; i < a.length() && i < b.length(); i++) {
            if (a.charAt(i) == b.charAt(i)) {
                same++;
            }
        }
        return 1.0 * same / total;
    }

    public static void main(String[] args) {
//        try {
//            ArrayList<String> a = FileHash.getSegWordsFromFile("D:\\testdata2\\未发布\\64929740.txt");
//
//            ArrayList<String> b = FileHash.getSegWordsFromFile("D:\\testdata2\\未发布\\64929739.txt");
//            System.out.println( similarity(a, b));
//        } catch (IOException e) {
//
//        }


        if (args.length != 2) {
            System.out.println("usage: java -jar CheckDuplication input_file index_file");
            return;
        }
        try {
            String hash = FileHash.getSimHash(args[0]);
            List<String> result = new ArrayList<String>();

            FileInputStream fis = new FileInputStream(args[1]);
            InputStreamReader isr = new InputStreamReader(fis, "UTF-8");
            Scanner sc = new Scanner(isr);
            while (sc.hasNext()) {
                String line = sc.nextLine();
                String[] part = line.split(" ");
                double sim = hashSimilarity(part[1], hash);
                if (sim > 0.6) { //simhash 足够相似的拿来深度比较
                    result.add(sim + " " + part[0]);
                }
            }

            if (result.size() == 0) {
                System.out.println("cannot find duplication");
            } else {
                //按照simhash 的结果排序
                String hashResultArr[] = new String[result.size()];
                hashResultArr = result.toArray(hashResultArr);
                Arrays.sort(hashResultArr, Collections.reverseOrder());

                ArrayList<String> a = FileHash.getSegWordsFromFile(args[0]);

                int maxCompareDocs = 1000; //最多比较最相似的1000个文件，用来调节速度
                String ret[] = new String[result.size() > maxCompareDocs ? maxCompareDocs : result.size()];
                int index = 0;
                for (String s_ : hashResultArr) {
                    String s = s_.split(" ")[1];
                    ArrayList<String> b = FileHash.getSegWordsFromFile("/root/testdata2/all/" + s);
                    //ret.add();
                    ret[index++] = similarity(a, b) + " " + s;
                    if (index > maxCompareDocs)
                        break;
                }
                // ret.sort();
                Arrays.sort(ret, Collections.reverseOrder());
                for (String s : ret) {
                    System.out.println(s);
                }
            }
        } catch (IOException e) {
            e.printStackTrace();
        }

    }
}
