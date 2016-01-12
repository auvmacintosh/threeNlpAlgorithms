package net.licstar.extractor;

import com.sree.textbytes.readabilityBUNDLE.Article;
import com.sree.textbytes.readabilityBUNDLE.ContentExtractor;
import org.mozilla.universalchardet.UniversalDetector;

import java.io.*;

/**
 * Created by Siwei on 2016/1/6.
 */
public class Extractor {

    public Extractor() {
    }


    private String readFileAsString(String filePath)
            throws java.io.IOException {
        StringBuilder fileData = new StringBuilder(1000);
        FileInputStream fis = new FileInputStream(filePath);
        InputStreamReader isr = new InputStreamReader(fis, detectEncoding(filePath));
        BufferedReader reader = new BufferedReader(isr);
        char[] buf = new char[1024];
        int numRead = 0;
        while ((numRead = reader.read(buf)) != -1) {
            String readData = String.valueOf(buf, 0, numRead);
            fileData.append(readData);
            buf = new char[1024];
        }
        reader.close();
        return fileData.toString();
    }

    public String extractString(String str) throws Exception {
        if(str.isEmpty()) //空字符串直接不转换
            return "<title></title><content></content>";

        Article article = new Article();
        ContentExtractor ce = new ContentExtractor();

        article = ce.extractContent(str, "ReadabilitySnack");

        //System.out.println("Content : "+article.getCleanedArticleText());



        //JResult res = extractor.extractContent(str);
        StringBuilder sb = new StringBuilder();
        sb.append("<title>");
        sb.append(article.getTitle());
        sb.append("</title>");
        sb.append("\r\n");
        sb.append("<content>");

        sb.append(article.getCleanedArticleText());
       // for (String t : res.getTextList()) {
      //      sb.append(t);
     //       sb.append("\r\n");
     //   }
        sb.append("</content>");
       // sb.append(article.getCleanedDocument().body().toString());

        return sb.toString();
    }


    public void writeStringToFile(String filePath, String content) {
        try {
            FileWriter fw = new FileWriter(filePath, false);
            BufferedWriter bw = new BufferedWriter(fw);
            bw.append(content);
            bw.close();
            fw.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private String detectEncoding(String path) throws IOException {
        byte[] buf = new byte[4096];
        String fileName = path;
        java.io.FileInputStream fis = new java.io.FileInputStream(fileName);

        // (1)
        UniversalDetector detector = new UniversalDetector(null);

        // (2)
        int nread;
        while ((nread = fis.read(buf)) > 0 && !detector.isDone()) {
            detector.handleData(buf, 0, nread);
        }
        // (3)
        detector.dataEnd();

        // (4)
        String encoding = detector.getDetectedCharset();

        // (5)
        detector.reset();

        if (encoding != null) {
            return encoding;
        } else {
            System.err.println("Unknown encoding: " + fileName);
            return "UTF-8";
        }
    }

    public void extractFile(String inputPath, String outputPath) throws Exception {
        String res = extractString(readFileAsString(inputPath));
        writeStringToFile(outputPath, res);
    }

    private static String combine(String path1, String path2) {
        File file1 = new File(path1);
        File file2 = new File(file1, path2);
        return file2.getPath();
    }

    /**
     * 处理inputPath目录下的所有html文件，结果存于outputPath下
     *
     * @param inputPath
     * @param outputPath
     */
    public void extractDir(String inputPath, String outputPath) {
        File dir = new File(inputPath);
        if (dir.exists()) {
            File[] files = dir.listFiles();
            for (File file : files) {
                if (!file.isDirectory()) {
                    try {
                        extractFile(file.getAbsolutePath(), combine(outputPath, file.getName()));
//EncodingDetector ed=new EncodingDetector();
                        // System.out.println( detectEncoding(file.getAbsolutePath()));
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                    // System.out.println(file.getName());
                }
            }
        } else {
            System.out.println("文件不存在!");
        }

    }


    public static void main(String[] args) {
        Extractor extractor = new Extractor();
        extractor.extractDir("F:\\喵\\down", "F:\\喵\\contentr1s");
    }

}
