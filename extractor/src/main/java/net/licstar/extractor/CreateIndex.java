package net.licstar.extractor;

import org.mozilla.universalchardet.UniversalDetector;

import java.io.*;
import java.security.MessageDigest;

/**
 * Created by licstar on 2016/2/3.
 */
public class CreateIndex {
    private final static String MD5(String s) {
        char hexDigits[]={'0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F'};
        try {
            byte[] btInput = s.getBytes();
            // 获得MD5摘要算法的 MessageDigest 对象
            MessageDigest mdInst = MessageDigest.getInstance("MD5");
            // 使用指定的字节更新摘要
            mdInst.update(btInput);
            // 获得密文
            byte[] md = mdInst.digest();
            // 把密文转换成十六进制的字符串形式
            int j = md.length;
            char str[] = new char[j * 2];
            int k = 0;
            for (int i = 0; i < j; i++) {
                byte byte0 = md[i];
                str[k++] = hexDigits[byte0 >>> 4 & 0xf];
                str[k++] = hexDigits[byte0 & 0xf];
            }
            return new String(str);
        } catch (Exception e) {
            e.printStackTrace();
            return null;
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
    /**
     * 处理inputPath目录下的所有html文件，结果存于outputFile文件
     *
     * @param inputPath
     * @param outputFile
     */
    public void extractDir(String inputPath, String outputFile) throws IOException {
        File dir = new File(inputPath);
        FileWriter fw = new FileWriter(outputFile, false);
        BufferedWriter bw = new BufferedWriter(fw);


        if (dir.exists()) {
            File[] files = dir.listFiles();
            for (File file : files) {
                if (!file.isDirectory()) {
                    try {
                        bw.append(file.getName());
                        bw.append(" ");
                        bw.append(MD5(readFileAsString(file.getAbsolutePath())));
                        bw.append("\n");
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

        bw.close();
        fw.close();
    }


    public static void main(String[] args) {
        if(args.length != 2){
            System.out.println("usage: java -jar CreateIndex input_dir output_index_file");
            return;
        }
        CreateIndex createIndex = new CreateIndex();
        try {
            createIndex.extractDir(args[0], args[1]);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }


}
