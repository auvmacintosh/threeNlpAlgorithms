package net.licstar.extractor;

import org.mozilla.universalchardet.UniversalDetector;

import java.io.*;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.util.regex.Pattern;

import com.chenlb.mmseg4j.*;

/**
 * 得到文件的hash值，支持MD5和SimHash
 * Created by licstar on 2016/2/25.
 */
public class FileHash {
    private final static String MD5(String s) {
        char hexDigits[] = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F'};
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


    static private String detectEncoding(String path) throws IOException {
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

    static private String readFileAsString(String filePath)
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

    static final public String getMD5(String file) throws IOException {
        return MD5(readFileAsString(file));
    }

    static private ArrayList<String> segText(String text, Seg seg) {
        ArrayList<String> result = new ArrayList<String>();
        MMSeg mmSeg = new MMSeg(new StringReader(text), seg);
        try {
            Word word = null;
            while ((word = mmSeg.next()) != null) {
                result.add(word.getString());
            }
        } catch (IOException ex) {
            throw new RuntimeException(ex);
        }
        return result;
    }

    private static final Dictionary DIC = Dictionary.getInstance();
    private static final SimpleSeg SIMPLE_SEG = new SimpleSeg(DIC);
    private static final ComplexSeg COMPLEX_SEG = new ComplexSeg(DIC);
    private static final MaxWordSeg MAX_WORD_SEG = new MaxWordSeg(DIC);

    static final public String getSimHash(String file) throws IOException {
        String text = readFileAsString(file);

        //1.解析指定格式
        String content = htmlRemoveTag(text);

        //2.分词
        ArrayList<String> seg = segText(content, COMPLEX_SEG);

        //3.固定的随机embedding，求和
        double[] sum = new double[SimHashBits];
        for (int i = 0; i < SimHashBits; i++) {
            sum[i] = 0;
        }
        for (String s : seg) {
            double[] x = getWordVector(s);
            for (int i = 0; i < SimHashBits; i++) {
                sum[i] += x[i];
            }
        }

        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < SimHashBits; i++) {
            if (sum[i] >= 0) {
                sb.append("1");
            } else {
                sb.append("0");
            }
        }
        return sb.toString();
    }

    /**
     * 获取每个词的词向量
     *
     * @param word
     * @return
     */
    static final public double[] getWordVector(String word) {
        double[] result = new double[SimHashBits];
        Random r = new Random(word.hashCode());
        for (int i = 0; i < SimHashBits; i++) {
            result[i] = r.nextDouble() - 0.5;
        }
        return result;
    }

    public static final int SimHashBits = 16;

    /**
     * 删除Html标签
     *
     * @param inputString
     * @return
     */
    public static String htmlRemoveTag(String inputString) {
        if (inputString == null)
            return null;
        String htmlStr = inputString; // 含html标签的字符串
        String textStr = "";
        java.util.regex.Pattern p_script;
        java.util.regex.Matcher m_script;
        java.util.regex.Pattern p_style;
        java.util.regex.Matcher m_style;
        java.util.regex.Pattern p_html;
        java.util.regex.Matcher m_html;
        try {
            //定义script的正则表达式{或<script[^>]*?>[\\s\\S]*?<\\/script>
            //String regEx_script = "<[\\s]*?script[^>]*?>[\\s\\S]*?<[\\s]*?\\/[\\s]*?script[\\s]*?>";
            //定义style的正则表达式{或<style[^>]*?>[\\s\\S]*?<\\/style>
            //String regEx_style = "<[\\s]*?style[^>]*?>[\\s\\S]*?<[\\s]*?\\/[\\s]*?style[\\s]*?>";
            String regEx_html = "<[^>]+>"; // 定义HTML标签的正则表达式
            /*p_script = Pattern.compile(regEx_script, Pattern.CASE_INSENSITIVE);
            m_script = p_script.matcher(htmlStr);
            htmlStr = m_script.replaceAll(""); // 过滤script标签
            p_style = Pattern.compile(regEx_style, Pattern.CASE_INSENSITIVE);
            m_style = p_style.matcher(htmlStr);
            htmlStr = m_style.replaceAll(""); // 过滤style标签*/
            p_html = Pattern.compile(regEx_html, Pattern.CASE_INSENSITIVE);
            m_html = p_html.matcher(htmlStr);
            htmlStr = m_html.replaceAll(""); // 过滤html标签
            textStr = htmlStr;
        } catch (Exception e) {
            e.printStackTrace();
        }
        return textStr;// 返回文本字符串
    }


    public static void main(String[] args) {
        try {
            System.out.println(getSimHash("D:\\testdata2\\已发布\\64740808.txt"));
        } catch (IOException e) {
            e.printStackTrace();
        }
        return;


/*
        if(args.length != 2){
            System.out.println("usage: java -jar CreateIndex input_dir output_index_file");
            return;
        }
        CreateIndex createIndex = new CreateIndex();
        try {
            createIndex.extractDir(args[0], args[1]);
        } catch (IOException e) {
            e.printStackTrace();
        }*/
    }

}
