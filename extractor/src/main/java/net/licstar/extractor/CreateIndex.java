package net.licstar.extractor;

import java.io.*;

/**
 * Created by licstar on 2016/2/3.
 */
public class CreateIndex {
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
                        bw.append(FileHash.getSimHash(file.getAbsolutePath()));
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
